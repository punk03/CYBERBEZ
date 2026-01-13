"""Syslog collector."""

import asyncio
import socket
from typing import Dict, Any, Optional
from datetime import datetime

from backend.ingestion.collectors.base import BaseCollector
from backend.common.logging import get_logger

logger = get_logger(__name__)


class SyslogCollector(BaseCollector):
    """Syslog collector for receiving syslog messages."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 514, config: Optional[Dict[str, Any]] = None):
        """
        Initialize syslog collector.
        
        Args:
            host: Host to bind to
            port: Port to listen on
            config: Additional configuration
        """
        super().__init__("syslog", config)
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self._queue: asyncio.Queue = asyncio.Queue()
    
    async def start(self) -> None:
        """Start syslog collector."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.setblocking(False)
        
        logger.info(f"Syslog collector started on {self.host}:{self.port}")
        
        # Start receiving loop
        self._task = asyncio.create_task(self._receive_loop())
    
    async def stop(self) -> None:
        """Stop syslog collector."""
        self.running = False
        if self._task:
            self._task.cancel()
        if self.socket:
            self.socket.close()
        logger.info("Syslog collector stopped")
    
    async def _receive_loop(self) -> None:
        """Receive syslog messages loop."""
        loop = asyncio.get_event_loop()
        
        while self.running:
            try:
                data, addr = await loop.sock_recvfrom(self.socket, 8192)
                message = data.decode("utf-8", errors="ignore")
                
                log_entry = {
                    "source": "syslog",
                    "host": addr[0],
                    "port": addr[1],
                    "message": message,
                    "timestamp": datetime.utcnow().isoformat(),
                    "raw": message,
                }
                
                await self._queue.put(log_entry)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error receiving syslog message: {e}")
                await asyncio.sleep(0.1)
    
    async def collect(self) -> Optional[Dict[str, Any]]:
        """Collect a log entry from queue."""
        try:
            return await asyncio.wait_for(self._queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            return None
