#!/usr/bin/env python3

import json
import logging
import time
import uuid
import threading
import schedule
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
import os
import hashlib

# Local imports
from .auditor import RoyaltyAuditor
from .pro_integration import PROIntegration
from .metadata_matcher import MetadataMatcher

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SessionCollector:
    """
    Session-based collector for royalty data that runs in timed loops
    
    This agent continuously collects and monitors royalty data across multiple sources,
    tracking detailed timing and attribution information to ensure proper credit 
    for funds recovered by the agency.
    """
    
    def __init__(self, config_path: Optional[str] = None, session_dir: Optional[str] = None):
        """
        Initialize the session collector
        
        Args:
            config_path: Path to configuration file (optional)
            session_dir: Directory to store session data (optional)
        """
        self.session_id = str(uuid.uuid4())
        self.session_start_time = datetime.now()
        self.session_dir = self._setup_session_dir(session_dir)
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.auditor = RoyaltyAuditor()
        self.pro_integration = PROIntegration()
        self.metadata_matcher = MetadataMatcher()
        
        # Tracking data
        self.discovery_registry = {}  # Tracks all discoveries with timestamps and attribution
        self.monitoring_sources = set()  # PROs and sources being monitored
        self.search_history = []  # History of all searches and their results
        self.fund_discoveries = {}  # Discovered funds with detailed provenance
        
        # Scheduling
        self.scheduler = schedule.Scheduler()
        self._setup_scheduled_tasks()
        
        # Session state
        self.is_running = False
        self.collection_thread = None
        
        logger.info(f"Session collector initialized with ID: {self.session_id}")
    
    def _setup_session_dir(self, session_dir: Optional[str]) -> Path:
        """Set up session directory for storing all session data"""
        if session_dir:
            base_dir = Path(session_dir)
        else:
            base_dir = Path(__file__).parent.parent.parent / "sessions"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_path = base_dir / f"session_{timestamp}_{self.session_id[:8]}"
        session_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (session_path / "discoveries").mkdir(exist_ok=True)
        (session_path / "reports").mkdir(exist_ok=True)
        (session_path / "scans").mkdir(exist_ok=True)
        (session_path / "audit_trails").mkdir(exist_ok=True)
        
        return session_path
    
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration or use defaults"""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        
        # Default configuration 
        return {
            # Collection intervals (in minutes)
            "collection_intervals": {
                "quick_scan": 15,
                "detailed_scan": 120,
                "deep_analysis": 1440,  # Daily
            },
            # PROs to monitor
            "monitored_pros": [
                "ascap", "bmi", "sesac", "soundexchange", 
                "hfa", "mlc", "ppl", "prs"
            ],
            # Platforms to monitor
            "monitored_platforms": [
                "spotify", "apple_music", "youtube", "amazon_music",
                "deezer", "tidal", "pandora"
            ],
            # Timing parameters
            "search_timeout": 300,  # seconds
            "retry_interval": 60,  # seconds
            "max_retries": 3,
            # Attribution parameters
            "agency_identifier": "MESA-AI-GUARDIAN",
            "attribution_confidence_threshold": 0.85,
            "fund_verification_required": True,
            # Reporting
            "generate_interim_reports": True,
            "report_interval": 1440  # minutes (daily)
        }
    
    def _setup_scheduled_tasks(self):
        """Set up scheduled collection tasks based on configuration"""
        # Quick scans
        quick_interval = self.config["collection_intervals"]["quick_scan"]
        schedule.every(quick_interval).minutes.do(self.run_quick_scan)
        
        # Detailed scans
        detailed_interval = self.config["collection_intervals"]["detailed_scan"]
        schedule.every(detailed_interval).minutes.do(self.run_detailed_scan)
        
        # Deep analysis
        deep_interval = self.config["collection_intervals"]["deep_analysis"]
        schedule.every(deep_interval).minutes.do(self.run_deep_analysis)
        
        # Reporting
        if self.config["generate_interim_reports"]:
            report_interval = self.config["report_interval"]
            schedule.every(report_interval).minutes.do(self.generate_attribution_report)
    
    def start_collection(self, run_immediately=True):
        """Start the collection process in a background thread"""
        if self.is_running:
            logger.warning("Collection already running")
            return
        
        self.is_running = True
        
        # Run immediate scans if requested
        if run_immediately:
            self.run_quick_scan()
        
        # Start the scheduler in a background thread
        self.collection_thread = threading.Thread(target=self._collection_loop)
        self.collection_thread.daemon = True
        self.collection_thread.start()
        
        logger.info(f"Collection started in session {self.session_id}")
    
    def stop_collection(self):
        """Stop the collection process"""
        if not self.is_running:
            logger.warning("Collection not running")
            return
        
        self.is_running = False
        if self.collection_thread:
            self.collection_thread.join(timeout=10)
        
        logger.info(f"Collection stopped in session {self.session_id}")
        
        # Generate final report
        self.generate_attribution_report(is_final=True)
    
    def _collection_loop(self):
        """Main collection loop that runs scheduled tasks"""
        while self.is_running:
            self.scheduler.run_pending()
            time.sleep(1)
    
    def _generate_discovery_id(self, discovery_data: Dict) -> str:
        """Generate a unique ID for a discovery based on its content"""
        # Create a stable representation of the discovery for hashing
        data_str = json.dumps(discovery_data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]
    
    def _register_discovery(self, discovery_type: str, source: str, 
                           discovery_data: Dict, confidence: float) -> str:
        """
        Register a discovery in the tracking system
        
        Args:
            discovery_type: Type of discovery (black_box, metadata, etc.)
            source: Source of the discovery (PRO, platform)
            discovery_data: The discovery data
            confidence: Confidence score of the discovery
            
        Returns:
            Discovery ID
        """
        discovery_id = self._generate_discovery_id(discovery_data)
        
        # Check if this is already discovered
        if discovery_id in self.discovery_registry:
            logger.debug(f"Discovery {discovery_id} already registered, updating")
            # Update existing record
            self.discovery_registry[discovery_id]["last_seen"] = datetime.now().isoformat()
            self.discovery_registry[discovery_id]["seen_count"] += 1
            return discovery_id
        
        # Register new discovery
        self.discovery_registry[discovery_id] = {
            "id": discovery_id,
            "type": discovery_type,
            "source": source,
            "first_discovered": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat(),
            "seen_count": 1,
            "session_id": self.session_id,
            "agency_identifier": self.config["agency_identifier"],
            "confidence": confidence,
            "data": discovery_data
        }
        
        # Save discovery to disk
        self._save_discovery(discovery_id)
        
        logger.info(f"New {discovery_type} discovery registered: {discovery_id} from {source}")
        return discovery_id
    
    def _save_discovery(self, discovery_id: str):
        """Save a discovery to disk"""
        if discovery_id not in self.discovery_registry:
            return
        
        discovery = self.discovery_registry[discovery_id]
        discovery_file = self.session_dir / "discoveries" / f"{discovery_id}.json"
        
        with open(discovery_file, 'w') as f:
            json.dump(discovery, f, indent=2)
    
    def run_quick_scan(self):
        """
        Run a quick scan for black box funds across all monitored PROs
        This is a lightweight scan that checks for obvious issues
        """
        logger.info("Running quick scan for black box funds")
        scan_start_time = datetime.now()
        
        scan_results = {
            "scan_id": f"quick_{int(time.time())}",
            "scan_type": "quick",
            "start_time": scan_start_time.isoformat(),
            "monitored_pros": list(self.config["monitored_pros"]),
            "discoveries": []
        }
        
        # Run quick check on each monitored PRO
        for pro in self.config["monitored_pros"]:
            try:
                logger.debug(f"Quick scanning {pro}")
                
                # In a real implementation, we would query each PRO API
                # For the demo, we'll just simulate some discoveries
                
                # Simulate some black box funds
                if pro in ["ascap", "bmi", "soundexchange"]:
                    discovery_data = {
                        "pro": pro,
                        "potential_funds": True,
                        "fund_types": ["streaming", "performance"],
                        "estimated_amount": f"${(100 + hash(pro + self.session_id) % 900):.2f}"
                    }
                    
                    discovery_id = self._register_discovery(
                        discovery_type="black_box_quick",
                        source=pro,
                        discovery_data=discovery_data,
                        confidence=0.75 + (hash(pro) % 20) / 100
                    )
                    
                    scan_results["discoveries"].append(discovery_id)
            
            except Exception as e:
                logger.error(f"Error scanning {pro}: {str(e)}")
        
        # Complete the scan
        scan_end_time = datetime.now()
        scan_results["end_time"] = scan_end_time.isoformat()
        scan_results["duration_seconds"] = (scan_end_time - scan_start_time).total_seconds()
        
        # Save scan results
        scan_file = self.session_dir / "scans" / f"{scan_results['scan_id']}.json"
        with open(scan_file, 'w') as f:
            json.dump(scan_results, f, indent=2)
        
        logger.info(f"Quick scan completed with {len(scan_results['discoveries'])} potential discoveries")
        return scan_results
    
    def run_detailed_scan(self):
        """
        Run a detailed scan across all monitored sources
        This does deeper analysis of catalog data against PRO databases
        """
        logger.info("Running detailed scan for royalty discrepancies")
        scan_start_time = datetime.now()
        
        scan_results = {
            "scan_id": f"detailed_{int(time.time())}",
            "scan_type": "detailed",
            "start_time": scan_start_time.isoformat(),
            "monitored_pros": list(self.config["monitored_pros"]),
            "monitored_platforms": list(self.config["monitored_platforms"]),
            "discoveries": []
        }
        
        # This would involve:
        # 1. Scanning PRO databases for registration issues
        # 2. Comparing streaming platform data with PRO data
        # 3. Looking for metadata discrepancies
        
        # Simulate multiple types of discoveries
        discovery_types = [
            ("metadata_mismatch", "High confidence metadata mismatch found"),
            ("unregistered_work", "Work appears in usage but not registered"),
            ("ownership_split", "Ownership percentage discrepancy detected"),
            ("black_box_funds", "Unclaimed black box funds identified")
        ]
        
        # Simulate discoveries across different sources
        for pro in self.config["monitored_pros"][:3]:  # Limit to first 3 for demo
            for discovery_type, message in discovery_types:
                # Create a simulated discovery
                work_id = f"WORK{hash(pro + discovery_type) % 1000}"
                
                discovery_data = {
                    "pro": pro,
                    "work_id": work_id,
                    "type": discovery_type,
                    "message": message,
                    "details": f"Issue found in {pro} for work {work_id}",
                    "estimated_value": f"${(200 + hash(pro + discovery_type) % 800):.2f}"
                }
                
                # Add additional details based on discovery type
                if discovery_type == "metadata_mismatch":
                    discovery_data["field"] = "writer"
                    discovery_data["expected"] = "John A. Smith"
                    discovery_data["found"] = "John Smith"
                
                # Register the discovery
                confidence = 0.80 + (hash(pro + discovery_type) % 15) / 100
                discovery_id = self._register_discovery(
                    discovery_type=discovery_type,
                    source=pro,
                    discovery_data=discovery_data,
                    confidence=confidence
                )
                
                scan_results["discoveries"].append(discovery_id)
                
                # If this is a fund discovery, add to fund tracking
                if "estimated_value" in discovery_data:
                    self._track_potential_fund(
                        discovery_id=discovery_id,
                        source=pro,
                        work_id=work_id,
                        estimated_value=discovery_data["estimated_value"],
                        confidence=confidence
                    )
        
        # Complete the scan
        scan_end_time = datetime.now()
        scan_results["end_time"] = scan_end_time.isoformat()
        scan_results["duration_seconds"] = (scan_end_time - scan_start_time).total_seconds()
        
        # Save scan results
        scan_file = self.session_dir / "scans" / f"{scan_results['scan_id']}.json"
        with open(scan_file, 'w') as f:
            json.dump(scan_results, f, indent=2)
        
        logger.info(f"Detailed scan completed with {len(scan_results['discoveries'])} discoveries")
        return scan_results
    
    def run_deep_analysis(self):
        """
        Run a deep analysis of the entire catalog and all available data
        This is the most thorough scan that looks for complex patterns
        """
        logger.info("Running deep analysis of royalty data")
        scan_start_time = datetime.now()
        
        scan_results = {
            "scan_id": f"deep_{int(time.time())}",
            "scan_type": "deep",
            "start_time": scan_start_time.isoformat(),
            "discoveries": []
        }
        
        # This would involve:
        # 1. Complex pattern analysis across multiple PROs
        # 2. Historical trend analysis
        # 3. Cross-referencing multiple data sources
        # 4. Advanced metadata matching across sources
        
        # In a real implementation, this would use more sophisticated algorithms
        
        # Simulate a few high-value discoveries
        high_value_discoveries = [
            {
                "type": "catalog_wide_issue",
                "description": "Systematic metadata error affecting multiple works",
                "affected_works": [f"WORK{i+100}" for i in range(5)],
                "affected_pros": ["ascap", "bmi", "soundexchange"],
                "estimated_total_value": "$4,750.00",
                "root_cause": "Publisher name format inconsistency",
                "complexity": "high"
            },
            {
                "type": "historical_underpayment",
                "description": "Consistent underpayment over 4 quarters",
                "affected_periods": ["2022-Q1", "2022-Q2", "2022-Q3", "2022-Q4"],
                "platform": "spotify",
                "estimated_total_value": "$2,340.00",
                "root_cause": "Stream count discrepancy",
                "evidence": "Statistical analysis of play counts versus payments",
                "complexity": "medium"
            },
            {
                "type": "ownership_conflict",
                "description": "Conflicting ownership claims causing royalty withholding",
                "work_id": "WORK888",
                "pros_involved": ["ascap", "sesac"],
                "estimated_held_funds": "$1,890.00",
                "resolution_path": "Ownership verification and dual claim resolution",
                "complexity": "high" 
            }
        ]
        
        # Register these high-value discoveries
        for discovery in high_value_discoveries:
            discovery_id = self._register_discovery(
                discovery_type="deep_analysis",
                source="multi_source",
                discovery_data=discovery,
                confidence=0.92  # Deep analysis has high confidence
            )
            
            scan_results["discoveries"].append(discovery_id)
            
            # Track as potential fund with complex attribution
            estimated_value = discovery.get("estimated_total_value") or discovery.get("estimated_held_funds")
            if estimated_value:
                self._track_potential_fund(
                    discovery_id=discovery_id,
                    source="deep_analysis",
                    work_id=discovery.get("work_id", "multiple"),
                    estimated_value=estimated_value,
                    confidence=0.92,
                    complexity=discovery.get("complexity", "medium")
                )
        
        # Complete the scan
        scan_end_time = datetime.now()
        scan_results["end_time"] = scan_end_time.isoformat()
        scan_results["duration_seconds"] = (scan_end_time - scan_start_time).total_seconds()
        
        # Save scan results
        scan_file = self.session_dir / "scans" / f"{scan_results['scan_id']}.json"
        with open(scan_file, 'w') as f:
            json.dump(scan_results, f, indent=2)
        
        logger.info(f"Deep analysis completed with {len(scan_results['discoveries'])} significant discoveries")
        return scan_results
    
    def _track_potential_fund(self, discovery_id: str, source: str, work_id: str, 
                             estimated_value: str, confidence: float, complexity: str = "low"):
        """
        Track a potential fund for recovery with attribution data
        
        Args:
            discovery_id: ID of the associated discovery
            source: Source of the fund discovery
            work_id: ID of the work associated with the fund
            estimated_value: Estimated value of the fund
            confidence: Confidence in the discovery
            complexity: Complexity of the recovery (low, medium, high)
        """
        fund_id = f"FUND-{discovery_id}"
        
        if fund_id in self.fund_discoveries:
            # Update existing record
            self.fund_discoveries[fund_id]["last_updated"] = datetime.now().isoformat()
            return fund_id
            
        # Create new fund tracking record
        numeric_value = float(estimated_value.replace("$", "").replace(",", ""))
        
        self.fund_discoveries[fund_id] = {
            "fund_id": fund_id,
            "discovery_id": discovery_id,
            "source": source,
            "work_id": work_id,
            "estimated_value": estimated_value,
            "numeric_value": numeric_value,
            "discovery_time": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "session_id": self.session_id,
            "agency_identifier": self.config["agency_identifier"],
            "confidence": confidence,
            "status": "potential",
            "complexity": complexity,
            "attribution": {
                "discovered_by": self.config["agency_identifier"],
                "discovery_method": "ai_royalty_auditor",
                "attribution_confidence": confidence,
                "attribution_evidence": [
                    f"First discovered in session {self.session_id}",
                    f"Tracked in discovery {discovery_id}",
                    f"Timestamp: {datetime.now().isoformat()}"
                ]
            }
        }
        
        # Save to disk
        self._save_fund_discovery(fund_id)
        
        logger.info(f"New potential fund tracked: {fund_id} worth {estimated_value} from {source}")
        return fund_id
    
    def _save_fund_discovery(self, fund_id: str):
        """Save a fund discovery to disk"""
        if fund_id not in self.fund_discoveries:
            return
            
        fund = self.fund_discoveries[fund_id]
        fund_file = self.session_dir / "discoveries" / f"{fund_id}.json"
        
        with open(fund_file, 'w') as f:
            json.dump(fund, f, indent=2)
    
    def generate_attribution_report(self, is_final=False):
        """
        Generate a comprehensive report of all discoveries with attribution data
        
        Args:
            is_final: Whether this is the final report for the session
        """
        report_id = f"report_{int(time.time())}"
        if is_final:
            report_id = f"final_report_{int(time.time())}"
            
        logger.info(f"Generating {report_id} attribution report")
        
        # Gather all discoveries and funds
        all_discoveries = list(self.discovery_registry.values())
        all_funds = list(self.fund_discoveries.values())
        
        # Calculate statistics
        total_potential_value = sum(fund["numeric_value"] for fund in all_funds)
        
        # Generate the report
        report = {
            "report_id": report_id,
            "is_final": is_final,
            "session_id": self.session_id,
            "generation_time": datetime.now().isoformat(),
            "session_start_time": self.session_start_time.isoformat(),
            "session_duration_hours": (datetime.now() - self.session_start_time).total_seconds() / 3600,
            "agency_identifier": self.config["agency_identifier"],
            "statistics": {
                "total_discoveries": len(all_discoveries),
                "total_potential_funds": len(all_funds),
                "total_potential_value": f"${total_potential_value:,.2f}",
                "discovery_counts_by_type": self._count_discoveries_by_type(),
                "sources_monitored": list(self.config["monitored_pros"]) + list(self.config["monitored_platforms"])
            },
            "highest_value_discoveries": self._get_top_discoveries(5),
            "agency_attribution": {
                "agency": self.config["agency_identifier"],
                "discovery_method": "MESA Rights Vault AI Royalty Auditor",
                "attribution_strength": "strong",
                "digital_signature": self._generate_attribution_signature()
            }
        }
        
        # If final report, include all data
        if is_final:
            report["all_discoveries"] = all_discoveries
            report["all_funds"] = all_funds
        
        # Save report to disk
        report_file = self.session_dir / "reports" / f"{report_id}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Attribution report {report_id} generated")
        
        return report
    
    def _count_discoveries_by_type(self) -> Dict[str, int]:
        """Count discoveries by type"""
        counts = {}
        for discovery in self.discovery_registry.values():
            discovery_type = discovery["type"]
            counts[discovery_type] = counts.get(discovery_type, 0) + 1
        return counts
    
    def _get_top_discoveries(self, count: int) -> List[Dict]:
        """Get the top N discoveries by value"""
        # Sort funds by numeric value
        sorted_funds = sorted(
            self.fund_discoveries.values(),
            key=lambda x: x["numeric_value"],
            reverse=True
        )
        
        # Return the top N
        return sorted_funds[:count]
    
    def _generate_attribution_signature(self) -> str:
        """Generate a digital signature for attribution"""
        # In a real implementation, this would use cryptographic signatures
        signature_base = f"{self.config['agency_identifier']}:{self.session_id}:{int(time.time())}"
        return hashlib.sha256(signature_base.encode()).hexdigest()
    
    def scan_specific_catalog(self, catalog_data: Dict) -> Dict:
        """
        Run a targeted scan on a specific catalog
        
        Args:
            catalog_data: The catalog data to scan
            
        Returns:
            Scan results with discoveries
        """
        logger.info(f"Running targeted scan on catalog with {len(catalog_data.get('works', []))} works")
        
        scan_results = {
            "scan_id": f"targeted_{int(time.time())}",
            "scan_type": "targeted",
            "start_time": datetime.now().isoformat(),
            "catalog_id": catalog_data.get("catalog_id", "unknown"),
            "rights_holder": catalog_data.get("rights_holder", "unknown"),
            "discoveries": []
        }
        
        # Use the auditor to analyze the catalog
        analysis = self.auditor.analyze_catalog(catalog_data)
        
        # Register discoveries from the analysis
        for opportunity in analysis.get("recovery_opportunities", []):
            discovery_data = {
                "work_id": opportunity["work_id"],
                "issue": opportunity["issue"],
                "estimated_value": opportunity["estimated_value"],
                "actions": opportunity["actions"],
                "from_catalog_analysis": True
            }
            
            discovery_id = self._register_discovery(
                discovery_type="catalog_analysis",
                source="targeted_scan",
                discovery_data=discovery_data,
                confidence=opportunity["confidence"]
            )
            
            scan_results["discoveries"].append(discovery_id)
            
            # Track as potential fund
            self._track_potential_fund(
                discovery_id=discovery_id,
                source="targeted_scan",
                work_id=opportunity["work_id"],
                estimated_value=opportunity["estimated_value"],
                confidence=opportunity["confidence"]
            )
        
        # Complete the scan
        scan_results["end_time"] = datetime.now().isoformat()
        scan_results["summary"] = analysis["summary"]
        
        # Save scan results
        scan_file = self.session_dir / "scans" / f"{scan_results['scan_id']}.json"
        with open(scan_file, 'w') as f:
            json.dump(scan_results, f, indent=2)
        
        logger.info(f"Targeted scan completed with {len(scan_results['discoveries'])} discoveries")
        return scan_results

    def get_session_summary(self) -> Dict:
        """Get a summary of the current session"""
        total_value = sum(fund["numeric_value"] for fund in self.fund_discoveries.values())
        
        return {
            "session_id": self.session_id,
            "start_time": self.session_start_time.isoformat(),
            "current_time": datetime.now().isoformat(),
            "duration_hours": (datetime.now() - self.session_start_time).total_seconds() / 3600,
            "total_discoveries": len(self.discovery_registry),
            "total_funds": len(self.fund_discoveries),
            "total_value": f"${total_value:,.2f}",
            "is_running": self.is_running,
            "sources_monitored": list(self.config["monitored_pros"]) + list(self.config["monitored_platforms"]),
            "agency_identifier": self.config["agency_identifier"],
        } 