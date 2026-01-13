"""Traffic blocking mechanisms."""

from typing import Dict, Any, Optional, List

from backend.common.logging import get_logger

logger = get_logger(__name__)


class TrafficBlocking:
    """Traffic blocking manager."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize traffic blocking."""
        self.config = config or {}
        self.blocked_traffic: Dict[str, Dict[str, Any]] = {}
    
    async def block_traffic(
        self,
        source_ip: Optional[str] = None,
        dest_ip: Optional[str] = None,
        port: Optional[int] = None,
        protocol: Optional[str] = None,
        reason: str = "Security threat"
    ) -> bool:
        """
        Block specific traffic.
        
        Args:
            source_ip: Source IP address
            dest_ip: Destination IP address
            port: Port number
            protocol: Protocol (tcp, udp, etc.)
            reason: Reason for blocking
        
        Returns:
            True if successful
        """
        try:
            block_key = f"{source_ip or '*'}:{dest_ip or '*'}:{port or '*'}:{protocol or '*'}"
            
            block_info = {
                "source_ip": source_ip,
                "dest_ip": dest_ip,
                "port": port,
                "protocol": protocol,
                "reason": reason,
                "timestamp": None,
                "status": "blocked",
            }
            
            from datetime import datetime
            block_info["timestamp"] = datetime.utcnow().isoformat()
            
            self.blocked_traffic[block_key] = block_info
            
            logger.warning(
                f"Traffic blocked: {source_ip or '*'} -> {dest_ip or '*'} "
                f":{port or '*'} ({protocol or '*'}) - {reason}"
            )
            
            # Here you would integrate with firewall/network equipment
            # to actually block the traffic
            
            return True
        
        except Exception as e:
            logger.error(f"Error blocking traffic: {e}", exc_info=True)
            return False
    
    async def unblock_traffic(
        self,
        source_ip: Optional[str] = None,
        dest_ip: Optional[str] = None,
        port: Optional[int] = None,
        protocol: Optional[str] = None
    ) -> bool:
        """Unblock traffic."""
        try:
            block_key = f"{source_ip or '*'}:{dest_ip or '*'}:{port or '*'}:{protocol or '*'}"
            
            if block_key in self.blocked_traffic:
                del self.blocked_traffic[block_key]
                logger.info(f"Traffic unblocked: {block_key}")
                return True
            else:
                logger.warning(f"Traffic block not found: {block_key}")
                return False
        
        except Exception as e:
            logger.error(f"Error unblocking traffic: {e}", exc_info=True)
            return False
    
    def get_blocked_traffic(self) -> List[Dict[str, Any]]:
        """Get list of blocked traffic."""
        return list(self.blocked_traffic.values())
