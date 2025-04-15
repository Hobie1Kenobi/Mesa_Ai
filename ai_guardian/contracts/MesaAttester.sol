// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import {IEAS} from "./IEAS.sol";
import {ISchemaRegistry} from "./ISchemaRegistry.sol";
import {SchemaRecord} from "./ISchemaRegistry.sol"; // Import struct if needed directly
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol"; // Import Ownable

contract MesaAttester is Ownable { // Inherit Ownable
    // --- EAS Configuration ---
    // Base Sepolia EAS: 0x4200000000000000000000000000000000000021
    // Base Sepolia SchemaRegistry: 0x4200000000000000000000000000000000000020
    address private constant EAS_ADDRESS = 0x4200000000000000000000000000000000000021;
    address private constant SCHEMA_REGISTRY_ADDRESS = 0x4200000000000000000000000000000000000020;

    IEAS private immutable eas;
    ISchemaRegistry private immutable schemaRegistry;

    // --- MESA Schema ---
    // Example Schema: Attests to the verification status of a rights record hash
    // Fields:
    // - bytes32 rightsVaultRecordHash: The keccak256 hash stored in RightsVault
    // - string verificationContext: e.g., "PublisherInternalAudit", "ThirdPartyValidation"
    // - bool isVerified: True if the record passes the context's verification
    string public constant MESA_VERIFICATION_SCHEMA = "bytes32 rightsVaultRecordHash, string verificationContext, bool isVerified";
    bytes32 public mesaSchemaUID; // UID assigned by EAS SchemaRegistry

    // --- Events ---
    event SchemaRegistered(bytes32 indexed schemaUID);
    event VerificationAttested(bytes32 indexed attestationUID, bytes32 indexed rightsVaultRecordHash, string verificationContext, bool isVerified);
    event VerificationRevoked(bytes32 indexed attestationUID, bytes32 indexed rightsVaultRecordHash);

    // --- Constructor ---
    constructor() Ownable(msg.sender) { // Set initial owner
        eas = IEAS(EAS_ADDRESS);
        schemaRegistry = ISchemaRegistry(SCHEMA_REGISTRY_ADDRESS);
    }

    // --- Schema Registration ---
    /**
     * @notice Registers the MESA verification schema with the EAS SchemaRegistry.
     * @dev Should typically be called once by the contract deployer or admin.
     * @param _resolver Address of an optional schema resolver contract (0x0 for none).
     * @param _revocable Whether attestations using this schema should be revocable.
     */
    function registerMesaSchema(address _resolver, bool _revocable) external onlyOwner { // Add onlyOwner modifier
        require(mesaSchemaUID == bytes32(0), "Schema already registered");
        mesaSchemaUID = schemaRegistry.register(MESA_VERIFICATION_SCHEMA, _resolver, _revocable);
        emit SchemaRegistered(mesaSchemaUID);
    }

    // --- Attestation Creation ---
    /**
     * @notice Creates an EAS attestation confirming the verification status of a rights record.
     * @param _recipient The address receiving the attestation (can be address(0) for public).
     * @param _rightsVaultRecordHash The hash of the rights data from RightsVault.
     * @param _verificationContext A string describing how the verification was performed.
     * @param _isVerified The outcome of the verification.
     * @param _expirationTime Timestamp when the attestation expires (0 for none).
     * @param _refUID Optional UID of a referenced attestation (bytes32(0) for none).
     * @return The UID of the newly created attestation.
     */
    function attestVerification(
        address _recipient,
        bytes32 _rightsVaultRecordHash,
        string calldata _verificationContext,
        bool _isVerified,
        uint64 _expirationTime,
        bytes32 _refUID
    ) external returns (bytes32) { // Consider adding payable if EAS requires value
        require(mesaSchemaUID != bytes32(0), "MESA Schema not registered");

        bytes memory encodedData = abi.encode(_rightsVaultRecordHash, _verificationContext, _isVerified);

        SchemaRecord memory schemaRecord = schemaRegistry.getSchema(mesaSchemaUID);

        IEAS.AttestationRequestData memory reqData = IEAS.AttestationRequestData({
            recipient: _recipient,
            expirationTime: _expirationTime,
            revocable: schemaRecord.revocable, // Use schema's revocability setting
            refUID: _refUID,
            data: encodedData,
            value: 0 // Set to msg.value if sending ETH
        });

        IEAS.AttestationRequest memory req = IEAS.AttestationRequest({
            schema: mesaSchemaUID,
            data: reqData
        });

        bytes32 attestationUID = eas.attest{value: msg.value}(req); // Pass value if needed

        emit VerificationAttested(attestationUID, _rightsVaultRecordHash, _verificationContext, _isVerified);
        return attestationUID;
    }

    // --- Attestation Revocation ---
     /**
     * @notice Revokes a previously created verification attestation.
     * @dev Requires the schema to be registered as revocable. Only the original attester can revoke.
     * @param _attestationUID The UID of the attestation to revoke.
     * @param _rightsVaultRecordHash The associated rights hash (for event emission).
     */
    function revokeVerification(bytes32 _attestationUID, bytes32 _rightsVaultRecordHash) external { // Consider adding payable if EAS requires value
        require(mesaSchemaUID != bytes32(0), "MESA Schema not registered");

        IEAS.Attestation memory attestation = eas.getAttestation(_attestationUID);
        require(attestation.schema == mesaSchemaUID, "Attestation not for MESA schema");
        // require(attestation.attester == msg.sender, "Only attester can revoke"); // EAS handles this check

        IEAS.RevocationRequestData memory revData = IEAS.RevocationRequestData({
            uid: _attestationUID,
            value: 0 // Set to msg.value if sending ETH
        });

         IEAS.RevocationRequest memory req = IEAS.RevocationRequest({
            schema: mesaSchemaUID,
            data: revData
        });

        eas.revoke{value: msg.value}(req); // Pass value if needed

        emit VerificationRevoked(_attestationUID, _rightsVaultRecordHash);
    }

    // --- View Functions ---
    /**
     * @notice Checks if a given attestation UID represents a valid (non-revoked, non-expired) MESA verification.
     * @param _attestationUID The UID to check.
     * @return True if valid, false otherwise.
     */
    function isVerificationValid(bytes32 _attestationUID) external view returns (bool) {
         if (_attestationUID == bytes32(0)) {
            return false;
        }
        IEAS.Attestation memory attestation = eas.getAttestation(_attestationUID);
        // Check it exists, uses our schema, hasn't expired, and hasn't been revoked
        return attestation.uid != bytes32(0) &&
               attestation.schema == mesaSchemaUID &&
               (attestation.expirationTime == 0 || attestation.expirationTime > block.timestamp) &&
               attestation.revocationTime == 0;
    }

     /**
     * @notice Decodes and returns the data from a MESA verification attestation.
     * @param _attestationUID The UID of the attestation.
     * @return rightsVaultRecordHash The hash attested to.
     * @return verificationContext The context string.
     * @return isVerified The verification boolean.
     */
    function getDecodedVerificationData(bytes32 _attestationUID)
        external
        view
        returns (
            bytes32 rightsVaultRecordHash,
            string memory verificationContext,
            bool isVerified
        )
    {
        IEAS.Attestation memory attestation = eas.getAttestation(_attestationUID);
        require(attestation.uid != bytes32(0) && attestation.schema == mesaSchemaUID, "Invalid or non-MESA attestation");

        (rightsVaultRecordHash, verificationContext, isVerified) = abi.decode(attestation.data, (bytes32, string, bool));
    }
} 