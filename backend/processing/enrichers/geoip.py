"""GeoIP enricher for adding geographical information."""

from typing import Dict, Any, Optional
import ipaddress

from backend.processing.enrichers.base import BaseEnricher
from backend.common.logging import get_logger

logger = get_logger(__name__)


class GeoIPEnricher(BaseEnricher):
    """Enricher for adding GeoIP information."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize GeoIP enricher."""
        super().__init__("geoip", config)
        # For MVP, we'll use a simple IP-based approach
        # In production, integrate with MaxMind GeoIP2 or similar service
        self.enabled = config.get("enabled", True) if config else True
    
    def _extract_ip(self, log_entry: Dict[str, Any]) -> Optional[str]:
        """Extract IP address from log entry."""
        # Check common IP fields
        ip_fields = ["ip", "ip_address", "src_ip", "dst_ip", "client_ip", "remote_addr"]
        
        for field in ip_fields:
            if field in log_entry:
                ip = log_entry[field]
                if isinstance(ip, str):
                    try:
                        # Validate IP address
                        ipaddress.ip_address(ip)
                        return ip
                    except ValueError:
                        continue
        
        # Try to extract from message
        message = log_entry.get("message", "")
        if message:
            # Simple IP regex (basic implementation)
            import re
            ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
            matches = re.findall(ip_pattern, message)
            if matches:
                try:
                    ipaddress.ip_address(matches[0])
                    return matches[0]
                except ValueError:
                    pass
        
        return None
    
    def _get_geo_info(self, ip: str) -> Dict[str, Any]:
        """
        Get geographical information for IP address.
        
        Args:
            ip: IP address
        
        Returns:
            GeoIP information
        """
        # MVP implementation - return basic info
        # In production, use MaxMind GeoIP2 or similar
        try:
            ip_obj = ipaddress.ip_address(ip)
            
            # Check if private IP
            if ip_obj.is_private:
                return {
                    "ip": ip,
                    "type": "private",
                    "country": None,
                    "city": None,
                }
            
            # Check if reserved/multicast
            if ip_obj.is_reserved or ip_obj.is_multicast:
                return {
                    "ip": ip,
                    "type": "reserved",
                    "country": None,
                    "city": None,
                }
            
            # For public IPs, return placeholder
            # In production, this would query GeoIP database
            return {
                "ip": ip,
                "type": "public",
                "country": None,  # Would be filled from GeoIP DB
                "city": None,     # Would be filled from GeoIP DB
            }
        
        except ValueError:
            return {
                "ip": ip,
                "type": "invalid",
            }
    
    async def enrich(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich log entry with GeoIP information."""
        if not self.enabled:
            return log_entry
        
        try:
            ip = self._extract_ip(log_entry)
            if ip:
                geo_info = self._get_geo_info(ip)
                log_entry["geoip"] = geo_info
                logger.debug(f"Added GeoIP info for IP {ip}")
        
        except Exception as e:
            logger.warning(f"Error enriching with GeoIP: {e}")
        
        return log_entry
