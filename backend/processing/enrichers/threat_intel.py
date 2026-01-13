"""Threat intelligence enricher."""

from typing import Dict, Any, Optional, Set
import ipaddress

from backend.processing.enrichers.base import BaseEnricher
from backend.common.logging import get_logger

logger = get_logger(__name__)


class ThreatIntelEnricher(BaseEnricher):
    """Enricher for adding threat intelligence information."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize threat intelligence enricher."""
        super().__init__("threat_intel", config)
        self.enabled = config.get("enabled", True) if config else True
        
        # In-memory threat lists (MVP)
        # In production, use external threat intelligence feeds
        self.malicious_ips: Set[str] = set()
        self.suspicious_ips: Set[str] = set()
        
        # Load initial threat data if provided
        if config and "threat_lists" in config:
            self.malicious_ips = set(config["threat_lists"].get("malicious_ips", []))
            self.suspicious_ips = set(config["threat_lists"].get("suspicious_ips", []))
    
    def _extract_ip(self, log_entry: Dict[str, Any]) -> Optional[str]:
        """Extract IP address from log entry."""
        ip_fields = ["ip", "ip_address", "src_ip", "dst_ip", "client_ip", "remote_addr"]
        
        for field in ip_fields:
            if field in log_entry:
                ip = log_entry[field]
                if isinstance(ip, str):
                    try:
                        ipaddress.ip_address(ip)
                        return ip
                    except ValueError:
                        continue
        
        return None
    
    def _check_threat(self, ip: str) -> Dict[str, Any]:
        """
        Check if IP is in threat intelligence database.
        
        Args:
            ip: IP address
        
        Returns:
            Threat intelligence information
        """
        threat_info = {
            "ip": ip,
            "is_malicious": False,
            "is_suspicious": False,
            "threat_types": [],
            "confidence": 0,
        }
        
        if ip in self.malicious_ips:
            threat_info["is_malicious"] = True
            threat_info["threat_types"].append("malicious_ip")
            threat_info["confidence"] = 100
        
        if ip in self.suspicious_ips:
            threat_info["is_suspicious"] = True
            threat_info["threat_types"].append("suspicious_ip")
            threat_info["confidence"] = max(threat_info["confidence"], 50)
        
        return threat_info
    
    async def enrich(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich log entry with threat intelligence information."""
        if not self.enabled:
            return log_entry
        
        try:
            ip = self._extract_ip(log_entry)
            if ip:
                threat_info = self._check_threat(ip)
                if threat_info["is_malicious"] or threat_info["is_suspicious"]:
                    log_entry["threat_intel"] = threat_info
                    logger.warning(
                        f"Threat detected for IP {ip}: "
                        f"{threat_info['threat_types']}"
                    )
        
        except Exception as e:
            logger.warning(f"Error enriching with threat intel: {e}")
        
        return log_entry
    
    def add_malicious_ip(self, ip: str) -> None:
        """Add IP to malicious list."""
        self.malicious_ips.add(ip)
        logger.info(f"Added malicious IP: {ip}")
    
    def add_suspicious_ip(self, ip: str) -> None:
        """Add IP to suspicious list."""
        self.suspicious_ips.add(ip)
        logger.info(f"Added suspicious IP: {ip}")
