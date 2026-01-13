"""Asset information enricher."""

from typing import Dict, Any, Optional

from backend.processing.enrichers.base import BaseEnricher
from backend.common.logging import get_logger

logger = get_logger(__name__)


class AssetInfoEnricher(BaseEnricher):
    """Enricher for adding asset information."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize asset information enricher."""
        super().__init__("asset_info", config)
        self.enabled = config.get("enabled", True) if config else True
        
        # In-memory asset database (MVP)
        # In production, query from CMDB or asset management system
        self.asset_db: Dict[str, Dict[str, Any]] = {}
        
        # Load initial asset data if provided
        if config and "assets" in config:
            self.asset_db = config["assets"]
    
    def _extract_hostname(self, log_entry: Dict[str, Any]) -> Optional[str]:
        """Extract hostname from log entry."""
        hostname = (
            log_entry.get("host") or
            log_entry.get("hostname") or
            log_entry.get("server") or
            None
        )
        return hostname
    
    def _get_asset_info(self, hostname: str) -> Dict[str, Any]:
        """
        Get asset information for hostname.
        
        Args:
            hostname: Hostname or IP address
        
        Returns:
            Asset information
        """
        # Check asset database
        if hostname in self.asset_db:
            return self.asset_db[hostname]
        
        # Default asset info
        return {
            "hostname": hostname,
            "asset_type": "unknown",
            "criticality": "medium",
            "department": None,
            "owner": None,
        }
    
    async def enrich(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich log entry with asset information."""
        if not self.enabled:
            return log_entry
        
        try:
            hostname = self._extract_hostname(log_entry)
            if hostname:
                asset_info = self._get_asset_info(hostname)
                log_entry["asset"] = asset_info
                logger.debug(f"Added asset info for {hostname}")
        
        except Exception as e:
            logger.warning(f"Error enriching with asset info: {e}")
        
        return log_entry
    
    def add_asset(self, hostname: str, asset_info: Dict[str, Any]) -> None:
        """Add asset to database."""
        self.asset_db[hostname] = asset_info
        logger.info(f"Added asset: {hostname}")
