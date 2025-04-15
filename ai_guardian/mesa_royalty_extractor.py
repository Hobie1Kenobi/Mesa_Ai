#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MESA Rights Vault - AI Guardian Royalty Extraction Module
Integrates with the AI-enhanced royalty scraper to extract rights data
and prepares it for storage in the MESA Rights Vault blockchain.
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add the parent directory to the path to import the royalty scraper
sys.path.append(str(Path(__file__).parent.parent.parent))
from royalty_scraper.ai_enhanced_scraper import AIEnhancedRoyaltyScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(f"mesa_royalty_guardian_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("mesa_guardian")

class MESARoyaltyGuardian:
    """
    AI Guardian component for the MESA Rights Vault that extracts royalty data
    and prepares it for private blockchain storage with zero-knowledge proofs.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        use_tor: bool = True, 
        session_dir: Optional[str] = None,
        stealth_mode: bool = True
    ):
        self.api_key = api_key or os.environ.get("LLAMA_CLOUD_API_KEY")
        self.use_tor = use_tor
        self.stealth_mode = stealth_mode
        
        # Create a unique session directory if none provided
        if not session_dir:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_id = f"session_{timestamp}_{os.urandom(4).hex()}"
            self.session_dir = os.path.join(
                Path(__file__).parent, 
                "sessions", 
                session_id
            )
        else:
            self.session_dir = session_dir
            
        # Create session subdirectories
        self.reports_dir = os.path.join(self.session_dir, "reports")
        self.scans_dir = os.path.join(self.session_dir, "scans")
        self.discoveries_dir = os.path.join(self.session_dir, "discoveries")
        self.audit_trails_dir = os.path.join(self.session_dir, "audit_trails")
        
        for directory in [self.session_dir, self.reports_dir, self.scans_dir, 
                         self.discoveries_dir, self.audit_trails_dir]:
            os.makedirs(directory, exist_ok=True)
            
        logger.info(f"Initialized MESA Royalty Guardian with session at {self.session_dir}")
        
        # Initialize the AI enhanced scraper
        self.scraper = AIEnhancedRoyaltyScraper(
            api_key=self.api_key,
            use_tor=self.use_tor,
            output_dir=self.scans_dir,
            max_retries=3,
            delay_between_sites=30,
            stealth_mode=self.stealth_mode
        )
        
    def extract_rights_data(self, search_terms: List[str]) -> Dict[str, Any]:
        """
        Extract rights data from multiple sources and compile a comprehensive report.
        
        Args:
            search_terms: List of artists or songs to search for
            
        Returns:
            Dictionary with comprehensive rights data
        """
        logger.info(f"Starting rights extraction for: {', '.join(search_terms)}")
        
        # Run the AI-enhanced scraper for comprehensive data
        scraper_results = self.scraper.run_comprehensive_search(search_terms)
        
        # Save the initial scan results
        scan_file = os.path.join(self.scans_dir, f"raw_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(scan_file, 'w', encoding='utf-8') as f:
            json.dump(scraper_results, f, indent=2)
        logger.info(f"Raw scan data saved to {scan_file}")
        
        # Process and normalize the data for MESA vault
        processed_results = self._process_for_mesa_vault(scraper_results)
        
        # Save the processed discoveries
        discovery_file = os.path.join(self.discoveries_dir, f"processed_rights_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(discovery_file, 'w', encoding='utf-8') as f:
            json.dump(processed_results, f, indent=2)
        logger.info(f"Processed rights data saved to {discovery_file}")
        
        # Generate audit trail
        self._generate_audit_trail(search_terms, scraper_results, processed_results)
        
        # Create final report
        report = self._generate_final_report(search_terms, processed_results)
        
        return report
    
    def _process_for_mesa_vault(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process and normalize raw scraping data into the MESA Rights Vault format.
        
        Args:
            raw_data: Raw data from the scraper
            
        Returns:
            Processed data in MESA Rights Vault format
        """
        logger.info("Processing raw data into MESA Rights Vault format")
        
        # Extract and normalize PRO data
        normalized_rights = []
        
        # Process PRO data
        for pro_name, pro_data in raw_data.get("pro_data", {}).items():
            for item in pro_data:
                normalized_right = {
                    "work_title": item.get("title", "Unknown"),
                    "creators": [{"name": item.get("writer", "Unknown"), "role": "Writer"}],
                    "publishers": [{"name": item.get("publisher", "Unknown")}],
                    "identifiers": {
                        "pro": pro_name,
                        "ipi_cae": item.get("IPI_CAE", "")
                    },
                    "rights_info": {
                        "type": "musical_work",
                        "royalty_splits": self._extract_royalty_splits(item),
                        "source": pro_name
                    },
                    "verification_status": "extracted",
                    "extraction_timestamp": datetime.now().isoformat()
                }
                normalized_rights.append(normalized_right)
        
        # Process distribution platform data
        for platform_name, platform_data in raw_data.get("distribution_data", {}).items():
            for item in platform_data:
                normalized_right = {
                    "work_title": item.get("title", "Unknown"),
                    "creators": [{"name": item.get("artist", "Unknown"), "role": "Artist"}],
                    "publishers": [],
                    "identifiers": {
                        "platform": platform_name
                    },
                    "rights_info": {
                        "type": "recording",
                        "distribution_info": item.get("distribution_info", {}),
                        "source": platform_name
                    },
                    "verification_status": "extracted",
                    "extraction_timestamp": datetime.now().isoformat()
                }
                normalized_rights.append(normalized_right)
        
        # Group by work title and merge related entries
        grouped_rights = {}
        for right in normalized_rights:
            title = right["work_title"]
            if title not in grouped_rights:
                grouped_rights[title] = right
            else:
                # Merge creators
                existing_creators = [c["name"] for c in grouped_rights[title]["creators"]]
                for creator in right["creators"]:
                    if creator["name"] not in existing_creators:
                        grouped_rights[title]["creators"].append(creator)
                
                # Merge publishers
                existing_publishers = [p["name"] for p in grouped_rights[title]["publishers"]]
                for publisher in right["publishers"]:
                    if publisher["name"] not in existing_publishers:
                        grouped_rights[title]["publishers"].append(publisher)
                        
                # Update identifiers
                grouped_rights[title]["identifiers"].update(right["identifiers"])
                
                # Update rights info
                if "royalty_splits" in right["rights_info"] and "royalty_splits" in grouped_rights[title]["rights_info"]:
                    grouped_rights[title]["rights_info"]["royalty_splits"].extend(right["rights_info"]["royalty_splits"])
                elif "royalty_splits" in right["rights_info"]:
                    grouped_rights[title]["rights_info"]["royalty_splits"] = right["rights_info"]["royalty_splits"]
                    
                if "distribution_info" in right["rights_info"]:
                    grouped_rights[title]["rights_info"]["distribution_info"] = right["rights_info"]["distribution_info"]
        
        processed_data = {
            "rights_data": list(grouped_rights.values()),
            "search_terms": raw_data.get("search_terms", []),
            "sources": list(raw_data.get("pro_data", {}).keys()) + list(raw_data.get("distribution_data", {}).keys()),
            "processing_timestamp": datetime.now().isoformat()
        }
        
        return processed_data
    
    def _extract_royalty_splits(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract royalty splits from an item."""
        royalty_info = item.get("royalty_info", {})
        if not royalty_info:
            return []
            
        return [{
            "party": item.get("writer", "Unknown"),
            "role": royalty_info.get("role", "Writer"),
            "share": royalty_info.get("share", ""),
            "split": royalty_info.get("split", "")
        }]
    
    def _generate_audit_trail(self, search_terms: List[str], raw_data: Dict[str, Any], 
                             processed_data: Dict[str, Any]) -> None:
        """Generate audit trail for the extraction process."""
        audit_trail = {
            "search_terms": search_terms,
            "extraction_timestamp": datetime.now().isoformat(),
            "sources_accessed": list(raw_data.get("pro_data", {}).keys()) + list(raw_data.get("distribution_data", {}).keys()),
            "raw_data_size": self._get_object_size(raw_data),
            "processed_data_size": self._get_object_size(processed_data),
            "rights_extracted": len(processed_data.get("rights_data", [])),
            "extraction_summary": {
                "pro_rights": {pro: len(data) for pro, data in raw_data.get("pro_data", {}).items()},
                "platform_rights": {platform: len(data) for platform, data in raw_data.get("distribution_data", {}).items()}
            }
        }
        
        audit_file = os.path.join(self.audit_trails_dir, f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(audit_file, 'w', encoding='utf-8') as f:
            json.dump(audit_trail, f, indent=2)
        logger.info(f"Audit trail saved to {audit_file}")
    
    def _generate_final_report(self, search_terms: List[str], processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a final report with privacy considerations for the MESA vault."""
        total_rights = len(processed_data.get("rights_data", []))
        
        report = {
            "report_id": f"rights_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "search_terms": search_terms,
            "total_rights_discovered": total_rights,
            "sources": processed_data.get("sources", []),
            "summary": {
                "works_by_type": self._count_works_by_type(processed_data),
                "unique_creators": self._count_unique_creators(processed_data),
                "verification_status": self._count_verification_status(processed_data)
            },
            "privacy_level": "full_details",
            "rights_data": processed_data.get("rights_data", []),
            "timestamp": int(datetime.now().timestamp()),
            "notes": "Generated by MESA Rights Vault AI Guardian"
        }
        
        report_file = os.path.join(self.reports_dir, f"final_report_{int(datetime.now().timestamp())}.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Final report saved to {report_file}")
        
        return report
    
    def _count_works_by_type(self, processed_data: Dict[str, Any]) -> Dict[str, int]:
        """Count works by type."""
        types_count = {}
        for right in processed_data.get("rights_data", []):
            right_type = right.get("rights_info", {}).get("type", "unknown")
            types_count[right_type] = types_count.get(right_type, 0) + 1
        return types_count
    
    def _count_unique_creators(self, processed_data: Dict[str, Any]) -> int:
        """Count unique creators across all works."""
        unique_creators = set()
        for right in processed_data.get("rights_data", []):
            for creator in right.get("creators", []):
                unique_creators.add(creator.get("name", ""))
        return len(unique_creators)
    
    def _count_verification_status(self, processed_data: Dict[str, Any]) -> Dict[str, int]:
        """Count rights by verification status."""
        status_count = {}
        for right in processed_data.get("rights_data", []):
            status = right.get("verification_status", "unknown")
            status_count[status] = status_count.get(status, 0) + 1
        return status_count
    
    def _get_object_size(self, obj: Any) -> int:
        """Get the size of an object in bytes."""
        return len(json.dumps(obj).encode('utf-8'))

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="MESA Rights Vault AI Guardian")
    parser.add_argument("--search-terms", type=str, required=True,
                        help="Comma-separated list of search terms (artists, songs)")
    parser.add_argument("--session-dir", type=str,
                        help="Directory to store session data (will create if not exists)")
    parser.add_argument("--tor-enabled", action="store_true", default=True,
                        help="Use Tor for anonymous data extraction")
    parser.add_argument("--stealth-mode", action="store_true", default=True,
                        help="Enable stealth mode with human-like behavior")
    parser.add_argument("--api-key", type=str,
                        help="API key (for future external API integration)")
    
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    # Parse search terms from comma-separated string
    search_term_list = [term.strip() for term in args.search_terms.split(",")]
    
    guardian = MESARoyaltyGuardian(
        api_key=args.api_key,
        use_tor=args.tor_enabled,
        session_dir=args.session_dir,
        stealth_mode=args.stealth_mode
    )
    
    # Extract rights data
    report = guardian.extract_rights_data(search_term_list)
    
    logger.info(f"Rights extraction complete! Discovered {report['total_rights_discovered']} rights")
    logger.info(f"Session data saved to {guardian.session_dir}") 