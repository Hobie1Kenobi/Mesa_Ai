import json
from typing import Dict, List, Optional
from dataclasses import dataclass
import hashlib
from datetime import datetime

@dataclass
class MusicRight:
    title: str
    artist: str
    rights_holder: str
    rights_type: str  # e.g., "composition", "recording", "publishing"
    percentage: float
    territory: str
    start_date: str
    end_date: Optional[str]
    metadata: Dict

class RightsGuardian:
    def __init__(self):
        self.processed_rights = {}
        
    def process_rights_document(self, document: Dict) -> MusicRight:
        """
        Process a rights document and extract structured rights information
        """
        try:
            right = MusicRight(
                title=document.get('title', ''),
                artist=document.get('artist', ''),
                rights_holder=document.get('rights_holder', ''),
                rights_type=document.get('rights_type', ''),
                percentage=float(document.get('percentage', 0)),
                territory=document.get('territory', 'global'),
                start_date=document.get('start_date', datetime.now().isoformat()),
                end_date=document.get('end_date'),
                metadata=document.get('metadata', {})
            )
            
            # Generate a unique identifier for the right
            right_id = self._generate_right_id(right)
            self.processed_rights[right_id] = right
            
            return right
            
        except Exception as e:
            raise ValueError(f"Failed to process rights document: {str(e)}")
    
    def generate_smart_contract_params(self, right: MusicRight) -> Dict:
        """
        Convert a MusicRight object into smart contract parameters
        """
        return {
            "rightId": self._generate_right_id(right),
            "rightsHolder": right.rights_holder,
            "rightsType": right.rights_type,
            "percentage": int(right.percentage * 100),  # Convert to basis points
            "territory": right.territory,
            "startDate": right.start_date,
            "endDate": right.end_date or "",
            "metadataHash": self._hash_metadata(right.metadata)
        }
    
    def generate_privacy_proof(self, right: MusicRight, 
                             reveal_fields: List[str] = None) -> Dict:
        """
        Generate a privacy-preserving proof of rights ownership
        """
        if reveal_fields is None:
            reveal_fields = ["rights_holder", "percentage"]
            
        proof = {
            "rightId": self._generate_right_id(right),
            "proofType": "selective_disclosure",
            "revealedFields": {},
            "hiddenFields": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Add revealed fields
        for field in reveal_fields:
            if hasattr(right, field):
                proof["revealedFields"][field] = getattr(right, field)
                
        # Add hashed hidden fields
        for field in [f for f in right.__annotations__ if f not in reveal_fields]:
            if hasattr(right, field):
                value = getattr(right, field)
                if isinstance(value, (str, int, float)):
                    proof["hiddenFields"][field] = self._hash_value(str(value))
                    
        return proof
    
    def _generate_right_id(self, right: MusicRight) -> str:
        """
        Generate a unique identifier for a right
        """
        data = f"{right.title}:{right.artist}:{right.rights_holder}:{right.rights_type}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _hash_metadata(self, metadata: Dict) -> str:
        """
        Hash metadata for privacy-preserving storage
        """
        return hashlib.sha256(json.dumps(metadata, sort_keys=True).encode()).hexdigest()
    
    def _hash_value(self, value: str) -> str:
        """
        Hash a single value for privacy-preserving proofs
        """
        return hashlib.sha256(value.encode()).hexdigest() 