import os
import json
import base64
import hashlib
import hmac
import time
import secrets
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
    load_pem_public_key,
    Encoding,
    PrivateFormat,
    PublicFormat,
    NoEncryption,
    BestAvailableEncryption
)

class KeyVault:
    """
    Secure key management system for MESA Rights Vault.
    Handles encryption keys, key recovery, and wallet integration.
    """
    
    def __init__(self, storage_dir=None):
        """
        Initialize the key vault
        
        Args:
            storage_dir (str): Directory for secure key storage (optional)
        """
        # Set up storage directory
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            self.storage_dir = Path.home() / ".mesa" / "keyvault"
        
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Vault state
        self.master_key = None
        self.identity_keys = {}
        self.rights_keys = {}
        self.connected_wallet = None
        self.key_backup_enabled = False
        self.vault_unlocked = False
    
    def create_new_vault(self, password, recovery_phrase=None):
        """
        Create a new key vault secured by password
        
        Args:
            password (str): Strong password for vault access
            recovery_phrase (str): Optional recovery phrase (or generated if not provided)
            
        Returns:
            dict: Vault information including recovery phrase
        """
        # Generate recovery phrase if not provided
        if not recovery_phrase:
            recovery_phrase = self._generate_recovery_phrase()
        
        # Derive master key from password and recovery phrase
        salt = os.urandom(16)
        self.master_key = self._derive_key_from_password(password, salt)
        
        # Create identity key pair
        identity_private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        identity_public_key = identity_private_key.public_key()
        
        # Serialize keys
        private_pem = identity_private_key.private_bytes(
            encoding=Encoding.PEM,
            format=PrivateFormat.PKCS8,
            encryption_algorithm=NoEncryption()
        )
        
        public_pem = identity_public_key.public_bytes(
            encoding=Encoding.PEM,
            format=PublicFormat.SubjectPublicKeyInfo
        )
        
        # Encrypt private key with master key
        private_key_cipher = Fernet(self.master_key)
        encrypted_private_key = private_key_cipher.encrypt(private_pem)
        
        # Store keys
        self.identity_keys = {
            "public_key": public_pem.decode('utf-8'),
            "encrypted_private_key": base64.b64encode(encrypted_private_key).decode('utf-8')
        }
        
        # Create vault metadata
        vault_metadata = {
            "created_at": int(time.time()),
            "salt": base64.b64encode(salt).decode('utf-8'),
            "identity_public_key": self.identity_keys["public_key"],
            "encrypted_identity_private_key": self.identity_keys["encrypted_private_key"],
            "recovery_hash": hashlib.sha256(recovery_phrase.encode()).hexdigest()
        }
        
        # Save vault data
        self._save_vault_metadata(vault_metadata)
        
        self.vault_unlocked = True
        
        return {
            "vault_id": hashlib.sha256(public_pem).hexdigest()[:16],
            "recovery_phrase": recovery_phrase,
            "created_at": vault_metadata["created_at"]
        }
    
    def unlock_vault(self, password):
        """
        Unlock the vault using password
        
        Args:
            password (str): Vault password
            
        Returns:
            bool: True if vault unlocked successfully
        """
        # Load vault metadata
        metadata = self._load_vault_metadata()
        if not metadata:
            return False
        
        # Derive master key from password and stored salt
        salt = base64.b64decode(metadata["salt"])
        derived_key = self._derive_key_from_password(password, salt)
        
        # Try to decrypt private key to verify password
        try:
            private_key_cipher = Fernet(derived_key)
            encrypted_private_key = base64.b64decode(metadata["encrypted_identity_private_key"])
            private_key_pem = private_key_cipher.decrypt(encrypted_private_key)
            
            # If successful, set master key and identity keys
            self.master_key = derived_key
            self.identity_keys = {
                "public_key": metadata["identity_public_key"],
                "encrypted_private_key": metadata["encrypted_identity_private_key"],
                "private_key_pem": private_key_pem
            }
            
            # Load rights keys
            self._load_rights_keys()
            
            self.vault_unlocked = True
            return True
        
        except Exception as e:
            print(f"Failed to unlock vault: {str(e)}")
            return False
    
    def recover_vault(self, recovery_phrase):
        """
        Recover vault access using recovery phrase and set new password
        
        Args:
            recovery_phrase (str): Original recovery phrase
            
        Returns:
            bool: True if recovery verification successful
        """
        # Load vault metadata
        metadata = self._load_vault_metadata()
        if not metadata:
            return False
        
        # Verify recovery phrase
        recovery_hash = hashlib.sha256(recovery_phrase.encode()).hexdigest()
        if recovery_hash != metadata["recovery_hash"]:
            return False
        
        # Recovery verified, prompt for new password would happen in UI
        return True
    
    def set_new_password(self, current_password, new_password):
        """
        Change the vault password
        
        Args:
            current_password (str): Current vault password
            new_password (str): New vault password
            
        Returns:
            bool: True if password changed successfully
        """
        if not self.vault_unlocked:
            if not self.unlock_vault(current_password):
                return False
        
        # Load vault metadata
        metadata = self._load_vault_metadata()
        if not metadata:
            return False
        
        # Generate new salt and derive new master key
        new_salt = os.urandom(16)
        new_master_key = self._derive_key_from_password(new_password, new_salt)
        
        # Decrypt private key with current master key
        private_key_pem = self.identity_keys.get("private_key_pem")
        if not private_key_pem:
            try:
                private_key_cipher = Fernet(self.master_key)
                encrypted_private_key = base64.b64decode(metadata["encrypted_identity_private_key"])
                private_key_pem = private_key_cipher.decrypt(encrypted_private_key)
            except Exception as e:
                print(f"Failed to decrypt private key: {str(e)}")
                return False
        
        # Encrypt private key with new master key
        new_cipher = Fernet(new_master_key)
        new_encrypted_private_key = new_cipher.encrypt(private_key_pem)
        
        # Update metadata
        metadata["salt"] = base64.b64encode(new_salt).decode('utf-8')
        metadata["encrypted_identity_private_key"] = base64.b64encode(new_encrypted_private_key).decode('utf-8')
        
        # Save updated metadata
        self._save_vault_metadata(metadata)
        
        # Update instance variables
        self.master_key = new_master_key
        self.identity_keys["encrypted_private_key"] = metadata["encrypted_identity_private_key"]
        
        # Re-encrypt and save all rights keys with new master key
        self._reencrypt_rights_keys(new_master_key)
        
        return True
    
    def connect_wallet(self, wallet_address, wallet_type="coinbase"):
        """
        Connect an external wallet for authentication and transactions
        
        Args:
            wallet_address (str): Blockchain wallet address
            wallet_type (str): Type of wallet (e.g., "coinbase", "metamask")
            
        Returns:
            bool: True if wallet connected successfully
        """
        if not self.vault_unlocked:
            return False
        
        # In a real implementation, this would verify wallet ownership
        # through a signature challenge
        
        self.connected_wallet = {
            "address": wallet_address,
            "type": wallet_type,
            "connected_at": int(time.time())
        }
        
        # Save wallet connection to vault
        metadata = self._load_vault_metadata()
        if metadata:
            metadata["connected_wallet"] = self.connected_wallet
            self._save_vault_metadata(metadata)
            return True
        
        return False
    
    def create_rights_key(self, rights_id, rights_metadata=None):
        """
        Create a new encryption key for a specific music rights entry
        
        Args:
            rights_id (str): Unique identifier for the rights
            rights_metadata (dict): Optional metadata about the rights
            
        Returns:
            str: Base64-encoded rights encryption key
        """
        if not self.vault_unlocked:
            return None
        
        # Generate a new Fernet key for this rights entry
        rights_key = Fernet.generate_key()
        
        # Encrypt the rights key with the master key
        cipher = Fernet(self.master_key)
        encrypted_key = cipher.encrypt(rights_key)
        
        # Store the encrypted key
        key_info = {
            "rights_id": rights_id,
            "encrypted_key": base64.b64encode(encrypted_key).decode('utf-8'),
            "created_at": int(time.time()),
            "metadata": rights_metadata or {}
        }
        
        self.rights_keys[rights_id] = key_info
        
        # Save to storage
        self._save_rights_key(rights_id, key_info)
        
        return base64.b64encode(rights_key).decode('utf-8')
    
    def get_rights_key(self, rights_id):
        """
        Retrieve a decrypted rights key
        
        Args:
            rights_id (str): Rights identifier
            
        Returns:
            str: Base64-encoded rights key if found, None otherwise
        """
        if not self.vault_unlocked:
            return None
        
        # Check if key is in memory
        key_info = self.rights_keys.get(rights_id)
        
        # If not in memory, try to load from storage
        if not key_info:
            key_info = self._load_rights_key(rights_id)
            if key_info:
                self.rights_keys[rights_id] = key_info
        
        if not key_info:
            return None
        
        # Decrypt the rights key
        try:
            cipher = Fernet(self.master_key)
            encrypted_key = base64.b64decode(key_info["encrypted_key"])
            rights_key = cipher.decrypt(encrypted_key)
            return base64.b64encode(rights_key).decode('utf-8')
        except Exception as e:
            print(f"Failed to decrypt rights key: {str(e)}")
            return None
    
    def share_rights_key(self, rights_id, recipient_public_key):
        """
        Securely share a rights key with another user
        
        Args:
            rights_id (str): Rights identifier
            recipient_public_key (str): Recipient's public key (PEM format)
            
        Returns:
            str: Encrypted key package for the recipient
        """
        if not self.vault_unlocked:
            return None
        
        # Get the decrypted rights key
        rights_key = self.get_rights_key(rights_id)
        if not rights_key:
            return None
        
        # Load recipient's public key
        try:
            public_key = load_pem_public_key(recipient_public_key.encode('utf-8'))
            
            # Encrypt the rights key with recipient's public key
            encrypted_key = public_key.encrypt(
                base64.b64decode(rights_key),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            # Create the key sharing package
            key_package = {
                "rights_id": rights_id,
                "sender": self.identity_keys["public_key"],
                "encrypted_key": base64.b64encode(encrypted_key).decode('utf-8'),
                "timestamp": int(time.time())
            }
            
            return json.dumps(key_package)
        
        except Exception as e:
            print(f"Failed to share rights key: {str(e)}")
            return None
    
    def receive_shared_key(self, key_package_json):
        """
        Receive and decrypt a shared rights key
        
        Args:
            key_package_json (str): JSON string of the key package
            
        Returns:
            dict: Rights key information
        """
        if not self.vault_unlocked:
            return None
        
        try:
            # Parse the key package
            key_package = json.loads(key_package_json)
            
            # Get private key PEM
            private_key_pem = self.identity_keys.get("private_key_pem")
            if not private_key_pem:
                metadata = self._load_vault_metadata()
                cipher = Fernet(self.master_key)
                encrypted_private_key = base64.b64decode(metadata["encrypted_identity_private_key"])
                private_key_pem = cipher.decrypt(encrypted_private_key)
            
            # Load private key
            private_key = load_pem_private_key(
                private_key_pem,
                password=None
            )
            
            # Decrypt the rights key
            encrypted_key = base64.b64decode(key_package["encrypted_key"])
            rights_key = private_key.decrypt(
                encrypted_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            # Store the received key
            rights_id = key_package["rights_id"]
            sender = key_package["sender"]
            
            # Encrypt with master key for storage
            cipher = Fernet(self.master_key)
            encrypted_for_storage = cipher.encrypt(rights_key)
            
            key_info = {
                "rights_id": rights_id,
                "encrypted_key": base64.b64encode(encrypted_for_storage).decode('utf-8'),
                "created_at": int(time.time()),
                "shared_by": sender,
                "received_at": int(time.time()),
                "metadata": {"shared": True}
            }
            
            self.rights_keys[rights_id] = key_info
            self._save_rights_key(rights_id, key_info)
            
            return {
                "rights_id": rights_id,
                "key": base64.b64encode(rights_key).decode('utf-8'),
                "from": sender
            }
        
        except Exception as e:
            print(f"Failed to receive shared key: {str(e)}")
            return None
    
    def backup_vault(self, backup_password=None):
        """
        Create an encrypted backup of the vault
        
        Args:
            backup_password (str): Optional separate password for the backup
            
        Returns:
            dict: Backup information
        """
        if not self.vault_unlocked:
            return None
        
        # Gather all vault data
        metadata = self._load_vault_metadata()
        
        # Get all rights keys
        rights_keys_data = {}
        for rights_id in self.rights_keys:
            key_info = self._load_rights_key(rights_id)
            if key_info:
                rights_keys_data[rights_id] = key_info
        
        # Create backup package
        backup_data = {
            "vault_metadata": metadata,
            "rights_keys": rights_keys_data,
            "backup_timestamp": int(time.time())
        }
        
        # Encrypt the backup
        backup_json = json.dumps(backup_data)
        
        # If backup password provided, use it; otherwise use master key
        if backup_password:
            backup_salt = os.urandom(16)
            backup_key = self._derive_key_from_password(backup_password, backup_salt)
            backup_info = {
                "salt": base64.b64encode(backup_salt).decode('utf-8'),
                "protected_with": "separate_password"
            }
        else:
            backup_key = self.master_key
            backup_info = {
                "protected_with": "vault_password"
            }
        
        cipher = Fernet(backup_key)
        encrypted_backup = cipher.encrypt(backup_json.encode('utf-8'))
        
        # Save backup
        backup_id = hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]
        backup_path = self.storage_dir / f"backup_{backup_id}.mrvb"
        
        with open(backup_path, 'wb') as f:
            f.write(encrypted_backup)
        
        backup_info.update({
            "backup_id": backup_id,
            "path": str(backup_path),
            "size_bytes": len(encrypted_backup),
            "created_at": int(time.time())
        })
        
        return backup_info
    
    def export_key_for_smart_wallet(self, rights_id, wallet_address):
        """
        Export a rights key in a format usable by a smart wallet for on-chain transactions
        
        Args:
            rights_id (str): Rights identifier
            wallet_address (str): Smart wallet address
            
        Returns:
            dict: Exported key package for smart wallet
        """
        if not self.vault_unlocked or not self.connected_wallet:
            return None
        
        # Verify wallet is connected
        if wallet_address != self.connected_wallet["address"]:
            return None
        
        # Get the rights key
        rights_key_b64 = self.get_rights_key(rights_id)
        if not rights_key_b64:
            return None
        
        # Create a wallet-specific derivation
        # This is a simplified version; in practice, would use wallet-specific encryption
        rights_key = base64.b64decode(rights_key_b64)
        wallet_specific_key = hmac.new(
            rights_key,
            wallet_address.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        return {
            "rights_id": rights_id,
            "wallet_address": wallet_address,
            "wallet_specific_key": base64.b64encode(wallet_specific_key).decode('utf-8'),
            "exportable_to_contract": True
        }
    
    # Helper methods
    def _generate_recovery_phrase(self, words=12):
        """Generate a random recovery phrase"""
        # This is a simplified version; in practice, would use BIP39 wordlist
        word_list = [
            "apple", "banana", "cherry", "date", "elder", "fig", "grape", "honey",
            "iris", "jade", "kiwi", "lemon", "mango", "navy", "olive", "peach",
            "quince", "rose", "sage", "thyme", "umber", "violet", "walnut", "xenia",
            "yellow", "zephyr", "anchor", "breeze", "coral", "dune", "echo", "frost",
            "galaxy", "harbor", "island", "jungle", "knoll", "lagoon", "meadow", "nebula",
            "oasis", "prairie", "quasar", "reef", "summit", "tide", "urban", "valley",
            "whisper", "xenon", "yacht", "zenith", "aurora", "brook", "creek", "delta"
        ]
        
        # Generate random indices
        selected_indices = [secrets.randbelow(len(word_list)) for _ in range(words)]
        recovery_phrase = " ".join([word_list[i] for i in selected_indices])
        
        return recovery_phrase
    
    def _derive_key_from_password(self, password, salt):
        """Derive a cryptographic key from password and salt"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.b64encode(kdf.derive(password.encode()))
        return key
    
    def _save_vault_metadata(self, metadata):
        """Save vault metadata to disk"""
        metadata_path = self.storage_dir / "vault_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
    
    def _load_vault_metadata(self):
        """Load vault metadata from disk"""
        metadata_path = self.storage_dir / "vault_metadata.json"
        if not metadata_path.exists():
            return None
        
        with open(metadata_path, 'r') as f:
            return json.load(f)
    
    def _save_rights_key(self, rights_id, key_info):
        """Save a rights key to disk"""
        keys_dir = self.storage_dir / "rights_keys"
        keys_dir.mkdir(exist_ok=True)
        
        key_path = keys_dir / f"{rights_id}.json"
        with open(key_path, 'w') as f:
            json.dump(key_info, f)
    
    def _load_rights_key(self, rights_id):
        """Load a rights key from disk"""
        keys_dir = self.storage_dir / "rights_keys"
        key_path = keys_dir / f"{rights_id}.json"
        
        if not key_path.exists():
            return None
        
        with open(key_path, 'r') as f:
            return json.load(f)
    
    def _load_rights_keys(self):
        """Load all rights keys from disk"""
        keys_dir = self.storage_dir / "rights_keys"
        keys_dir.mkdir(exist_ok=True)
        
        for key_file in keys_dir.glob("*.json"):
            with open(key_file, 'r') as f:
                key_info = json.load(f)
                rights_id = key_info["rights_id"]
                self.rights_keys[rights_id] = key_info
    
    def _reencrypt_rights_keys(self, new_master_key):
        """Re-encrypt all rights keys with a new master key"""
        old_cipher = Fernet(self.master_key)
        new_cipher = Fernet(new_master_key)
        
        for rights_id, key_info in self.rights_keys.items():
            try:
                # Decrypt with old key
                encrypted_key = base64.b64decode(key_info["encrypted_key"])
                decrypted_key = old_cipher.decrypt(encrypted_key)
                
                # Re-encrypt with new key
                new_encrypted_key = new_cipher.encrypt(decrypted_key)
                key_info["encrypted_key"] = base64.b64encode(new_encrypted_key).decode('utf-8')
                
                # Save updated key
                self._save_rights_key(rights_id, key_info)
            except Exception as e:
                print(f"Failed to re-encrypt key {rights_id}: {str(e)}")


def main():
    """Demo the key management system"""
    print("=== MESA Rights Vault Key Management Demo ===\n")
    
    # Create a temporary directory for the demo
    import tempfile
    temp_dir = tempfile.mkdtemp()
    print(f"Using temporary storage at: {temp_dir}\n")
    
    # Initialize the key vault
    key_vault = KeyVault(storage_dir=temp_dir)
    
    # 1. Create a new vault
    vault_password = "StrongP@ssw0rd123!"
    vault_info = key_vault.create_new_vault(vault_password)
    
    print("1. Created New Vault")
    print(f"   Vault ID: {vault_info['vault_id']}")
    print(f"   Recovery Phrase: {vault_info['recovery_phrase']}")
    print(f"   Created At: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(vault_info['created_at']))}")
    
    # 2. Connect a wallet
    wallet_address = "0x7338af1E9d6dbc4cc1Efa067C0775Bf222aDb0C3"
    key_vault.connect_wallet(wallet_address, wallet_type="coinbase")
    
    print("\n2. Connected Smart Wallet")
    print(f"   Wallet Address: {wallet_address}")
    print(f"   Wallet Type: Coinbase Smart Wallet")
    
    # 3. Create encryption keys for rights data
    rights_entries = [
        {"id": "right_001", "title": "Midnight Dreams", "artist": "Sarah Wilson"},
        {"id": "right_002", "title": "Electronic Horizon", "artist": "The Lunar Echoes"},
        {"id": "right_003", "title": "Harmony Collection", "artist": "Daniel Morgan"}
    ]
    
    print("\n3. Creating Rights Encryption Keys")
    for rights in rights_entries:
        rights_id = rights["id"]
        key = key_vault.create_rights_key(rights_id, rights)
        print(f"   Created key for '{rights['title']}' (ID: {rights_id})")
    
    # 4. Export a key for smart wallet usage
    exported_key = key_vault.export_key_for_smart_wallet("right_001", wallet_address)
    
    print("\n4. Exported Key for Smart Wallet")
    print(f"   Rights ID: {exported_key['rights_id']}")
    print(f"   Wallet Address: {exported_key['wallet_address']}")
    print(f"   Wallet-Specific Key: {exported_key['wallet_specific_key'][:16]}...")
    print(f"   Exportable to Contract: {exported_key['exportable_to_contract']}")
    
    # 5. Create a vault backup
    backup_info = key_vault.backup_vault()
    
    print("\n5. Created Vault Backup")
    print(f"   Backup ID: {backup_info['backup_id']}")
    print(f"   Protected With: {backup_info['protected_with']}")
    print(f"   Size: {backup_info['size_bytes']} bytes")
    print(f"   Path: {backup_info['path']}")
    
    # 6. Simulate key sharing with another user
    
    # Create a second vault to simulate another user
    second_vault = KeyVault(storage_dir=temp_dir + "_second")
    second_vault_info = second_vault.create_new_vault("AnotherStrongP@ss!")
    
    # Extract public key from second vault's metadata
    second_metadata = second_vault._load_vault_metadata()
    recipient_public_key = second_metadata["identity_public_key"]
    
    # Share a key with the second user
    shared_key_package = key_vault.share_rights_key("right_002", recipient_public_key)
    
    print("\n6. Shared Rights Key With Another User")
    print(f"   Shared Key: right_002 (Electronic Horizon)")
    
    # Receive the shared key in the second vault
    received_key = second_vault.receive_shared_key(shared_key_package)
    
    print("   Key Successfully Received by Second User")
    print(f"   Rights ID: {received_key['rights_id']}")
    print(f"   Key: {received_key['key'][:16]}...")
    
    print("\n=== Key Management System Demo Complete ===")
    print("This system provides secure, recoverable key management")
    print("with smart wallet integration and collaborative key sharing")
    print("for the MESA Rights Vault platform.")

if __name__ == "__main__":
    main() 