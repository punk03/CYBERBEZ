"""Network isolation mechanisms."""

from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

from backend.common.logging import get_logger

logger = get_logger(__name__)


class NetworkIsolationBase(ABC):
    """Base class for network isolation."""
    
    @abstractmethod
    async def block_ip(self, ip: str, reason: str) -> bool:
        """Block IP address."""
        pass
    
    @abstractmethod
    async def unblock_ip(self, ip: str) -> bool:
        """Unblock IP address."""
        pass
    
    @abstractmethod
    async def block_port(self, ip: str, port: int, protocol: str = "tcp") -> bool:
        """Block port for IP address."""
        pass


class IPTablesIsolation(NetworkIsolationBase):
    """Network isolation using iptables."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize iptables isolation."""
        self.config = config or {}
        self.chain_name = config.get("chain_name", "PROKVANT_BLOCK") if config else "PROKVANT_BLOCK"
    
    async def block_ip(self, ip: str, reason: str) -> bool:
        """Block IP using iptables."""
        try:
            import subprocess
            
            # Create chain if it doesn't exist
            subprocess.run(
                ["sudo", "iptables", "-N", self.chain_name],
                check=False,
                capture_output=True
            )
            
            # Add rule to block IP
            result = subprocess.run(
                [
                    "sudo", "iptables", "-A", self.chain_name,
                    "-s", ip,
                    "-j", "DROP",
                    "-m", "comment", "--comment", f"PROKVANT: {reason}"
                ],
                check=True,
                capture_output=True
            )
            
            logger.info(f"Blocked IP {ip} using iptables: {reason}")
            return True
        
        except Exception as e:
            logger.error(f"Error blocking IP {ip} with iptables: {e}", exc_info=True)
            return False
    
    async def unblock_ip(self, ip: str) -> bool:
        """Unblock IP using iptables."""
        try:
            import subprocess
            
            result = subprocess.run(
                [
                    "sudo", "iptables", "-D", self.chain_name,
                    "-s", ip,
                    "-j", "DROP"
                ],
                check=True,
                capture_output=True
            )
            
            logger.info(f"Unblocked IP {ip} using iptables")
            return True
        
        except Exception as e:
            logger.error(f"Error unblocking IP {ip} with iptables: {e}", exc_info=True)
            return False
    
    async def block_port(self, ip: str, port: int, protocol: str = "tcp") -> bool:
        """Block port for IP."""
        try:
            import subprocess
            
            result = subprocess.run(
                [
                    "sudo", "iptables", "-A", self.chain_name,
                    "-s", ip,
                    "-p", protocol,
                    "--dport", str(port),
                    "-j", "DROP"
                ],
                check=True,
                capture_output=True
            )
            
            logger.info(f"Blocked port {port}/{protocol} for IP {ip}")
            return True
        
        except Exception as e:
            logger.error(f"Error blocking port {port} for IP {ip}: {e}", exc_info=True)
            return False


class NetworkIsolation:
    """Network isolation manager."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize network isolation."""
        self.config = config or {}
        isolation_type = config.get("type", "iptables") if config else "iptables"
        
        if isolation_type == "iptables":
            self.isolator = IPTablesIsolation(config.get("iptables", {}))
        else:
            raise ValueError(f"Unsupported isolation type: {isolation_type}")
    
    async def isolate(self, detection: Dict[str, Any]) -> Dict[str, Any]:
        """
        Isolate threat based on detection.
        
        Args:
            detection: Detection result
        
        Returns:
            Isolation result
        """
        result = {
            "success": False,
            "actions": [],
            "errors": [],
        }
        
        try:
            attack_type = detection.get("attack_type")
            source_ip = detection.get("source_ip") or detection.get("ip")
            
            if not source_ip:
                result["errors"].append("No source IP found in detection")
                return result
            
            # Block IP
            reason = f"{attack_type} attack detected"
            blocked = await self.isolator.block_ip(source_ip, reason)
            
            if blocked:
                result["actions"].append(f"Blocked IP {source_ip}")
                result["success"] = True
            else:
                result["errors"].append(f"Failed to block IP {source_ip}")
            
            # Block specific ports if detected
            port = detection.get("port")
            if port:
                protocol = detection.get("protocol", "tcp")
                port_blocked = await self.isolator.block_port(source_ip, port, protocol)
                if port_blocked:
                    result["actions"].append(f"Blocked port {port}/{protocol} for {source_ip}")
            
            logger.info(f"Isolation completed for {source_ip}: {result['actions']}")
        
        except Exception as e:
            logger.error(f"Error in isolation: {e}", exc_info=True)
            result["errors"].append(str(e))
        
        return result
