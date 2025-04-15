#!/usr/bin/env python3

import logging
from typing import Dict, List, Tuple, Optional, Any
import json
import re
from difflib import SequenceMatcher

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MetadataMatcher:
    """
    AI-powered metadata matching and correction system
    
    Uses advanced fuzzy matching, NLP techniques, and pattern recognition
    to identify and correct metadata discrepancies in music rights data.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize metadata matcher
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {
            "similarity_threshold": 0.85,
            "name_variations": True,
            "use_pattern_matching": True,
            "fuzzy_match_fields": ["artist", "writer", "title", "publisher"]
        }
        
        logger.info("Initialized metadata matcher")
    
    def calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate string similarity using sequence matcher
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Similarity score between 0 and 1
        """
        if not str1 or not str2:
            return 0.0
            
        # Normalize strings
        str1 = self._normalize_string(str1)
        str2 = self._normalize_string(str2)
        
        # Calculate similarity
        return SequenceMatcher(None, str1, str2).ratio()
    
    def _normalize_string(self, input_str: str) -> str:
        """Normalize string for comparison"""
        if not input_str:
            return ""
            
        # Convert to lowercase
        result = input_str.lower()
        
        # Remove special characters
        result = re.sub(r'[^\w\s]', '', result)
        
        # Normalize whitespace
        result = re.sub(r'\s+', ' ', result).strip()
        
        return result
    
    def find_matching_record(self, query_record: Dict, candidate_records: List[Dict], 
                            match_fields: Optional[List[str]] = None) -> Tuple[Optional[Dict], float]:
        """
        Find best matching record from candidates
        
        Args:
            query_record: Record to find match for
            candidate_records: List of potential matching records
            match_fields: Fields to use for matching
            
        Returns:
            Tuple of (best matching record, confidence score)
        """
        match_fields = match_fields or self.config.get("fuzzy_match_fields")
        
        best_match = None
        best_score = 0.0
        
        for candidate in candidate_records:
            score = self._calculate_record_similarity(query_record, candidate, match_fields)
            
            if score > best_score:
                best_score = score
                best_match = candidate
        
        threshold = self.config.get("similarity_threshold", 0.85)
        if best_score >= threshold:
            return best_match, best_score
        else:
            return None, best_score
    
    def _calculate_record_similarity(self, record1: Dict, record2: Dict, 
                                   fields: List[str]) -> float:
        """
        Calculate similarity between two records based on specific fields
        
        Args:
            record1: First record
            record2: Second record
            fields: Fields to compare
            
        Returns:
            Similarity score between 0 and 1
        """
        if not fields:
            return 0.0
            
        total_score = 0.0
        field_count = 0
        
        for field in fields:
            if field in record1 and field in record2:
                field_score = self.calculate_similarity(str(record1[field]), str(record2[field]))
                total_score += field_score
                field_count += 1
        
        return total_score / max(1, field_count)
    
    def generate_corrections(self, source_record: Dict, target_record: Dict) -> Dict:
        """
        Generate corrections to transform source record into target record
        
        Args:
            source_record: Original record with issues
            target_record: Target correct record
            
        Returns:
            Dictionary of corrections to apply
        """
        corrections = {}
        
        # Find fields that differ
        for field in target_record:
            if field in source_record:
                source_value = str(source_record[field])
                target_value = str(target_record[field])
                
                similarity = self.calculate_similarity(source_value, target_value)
                
                if similarity < 1.0:
                    corrections[field] = {
                        "from": source_value,
                        "to": target_value,
                        "confidence": similarity
                    }
        
        return {
            "source_id": source_record.get("id", "unknown"),
            "target_id": target_record.get("id", "unknown"),
            "corrections": corrections,
            "overall_confidence": self._calculate_overall_confidence(corrections)
        }
    
    def _calculate_overall_confidence(self, corrections: Dict) -> float:
        """Calculate overall confidence for corrections"""
        if not corrections:
            return 0.0
            
        confidences = [c.get("confidence", 0) for c in corrections.values()]
        return sum(confidences) / max(1, len(confidences))
    
    def analyze_name_variations(self, names: List[str]) -> Dict:
        """
        Analyze variations of a name to identify potential matches
        
        Args:
            names: List of name variations
            
        Returns:
            Analysis results with potential canonical form
        """
        if not names:
            return {"canonical": None, "variations": []}
            
        # Simple implementation - in a real system this would use more sophisticated
        # name matching algorithms with knowledge of name formats, abbreviations, etc.
        
        name_groups = {}
        
        # Group similar names
        for name in names:
            found_group = False
            normalized = self._normalize_string(name)
            
            for group_key in name_groups:
                if self.calculate_similarity(normalized, group_key) > 0.8:
                    name_groups[group_key].append(name)
                    found_group = True
                    break
            
            if not found_group:
                name_groups[normalized] = [name]
        
        # Find the largest group
        largest_group_key = max(name_groups, key=lambda k: len(name_groups[k]))
        largest_group = name_groups[largest_group_key]
        
        # Determine canonical form (longest name in the largest group)
        canonical = max(largest_group, key=len)
        
        # Collect all variations
        all_variations = []
        for group in name_groups.values():
            if group != largest_group:
                all_variations.extend(group)
        
        return {
            "canonical": canonical,
            "variations": all_variations,
            "confidence": len(largest_group) / len(names)
        }
    
    def extract_isrc_iswc(self, text: str) -> Dict:
        """
        Extract ISRC and ISWC codes from text
        
        Args:
            text: Text to extract from
            
        Returns:
            Dictionary with extracted codes
        """
        # ISRC format: CC-XXX-YY-NNNNN
        isrc_pattern = r'[A-Z]{2}-[A-Z0-9]{3}-\d{2}-\d{5}'
        
        # ISWC format: T-XXXXXXXX-Y
        iswc_pattern = r'T-\d{9}-\d'
        
        isrc_matches = re.findall(isrc_pattern, text)
        iswc_matches = re.findall(iswc_pattern, text)
        
        return {
            "isrc": isrc_matches,
            "iswc": iswc_matches
        } 