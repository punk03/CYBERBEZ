"""File watcher collector."""

import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

from backend.ingestion.collectors.base import BaseCollector
from backend.common.logging import get_logger

logger = get_logger(__name__)


class LogFileHandler(FileSystemEventHandler):
    """Handler for log file events."""
    
    def __init__(self, queue: asyncio.Queue, file_path: Path):
        """
        Initialize handler.
        
        Args:
            queue: Queue to put log entries
            file_path: Path to log file
        """
        self.queue = queue
        self.file_path = file_path
        self.last_position = 0
    
    def on_modified(self, event: FileModifiedEvent) -> None:
        """Handle file modification event."""
        if event.src_path == str(self.file_path):
            asyncio.create_task(self._read_new_lines())
    
    async def _read_new_lines(self) -> None:
        """Read new lines from file."""
        try:
            with open(self.file_path, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(self.last_position)
                new_lines = f.readlines()
                self.last_position = f.tell()
                
                for line in new_lines:
                    if line.strip():
                        log_entry = {
                            "source": "file",
                            "file_path": str(self.file_path),
                            "message": line.strip(),
                            "timestamp": datetime.utcnow().isoformat(),
                            "raw": line.strip(),
                        }
                        await self.queue.put(log_entry)
        except Exception as e:
            logger.error(f"Error reading file {self.file_path}: {e}")


class FileWatcherCollector(BaseCollector):
    """File watcher collector for monitoring log files."""
    
    def __init__(self, file_paths: List[str], config: Optional[Dict[str, Any]] = None):
        """
        Initialize file watcher collector.
        
        Args:
            file_paths: List of file paths to watch
            config: Additional configuration
        """
        super().__init__("file_watcher", config)
        self.file_paths = [Path(p) for p in file_paths]
        self.observer: Optional[Observer] = None
        self._queue: asyncio.Queue = asyncio.Queue()
        self.handlers: List[LogFileHandler] = []
    
    async def start(self) -> None:
        """Start file watcher."""
        self.observer = Observer()
        
        for file_path in self.file_paths:
            if not file_path.exists():
                logger.warning(f"File does not exist: {file_path}")
                continue
            
            handler = LogFileHandler(self._queue, file_path)
            self.handlers.append(handler)
            self.observer.schedule(handler, str(file_path.parent), recursive=False)
            
            # Read existing content
            await handler._read_new_lines()
        
        self.observer.start()
        logger.info(f"File watcher started for {len(self.file_paths)} files")
    
    async def stop(self) -> None:
        """Stop file watcher."""
        self.running = False
        if self.observer:
            self.observer.stop()
            self.observer.join()
        logger.info("File watcher stopped")
    
    async def collect(self) -> Optional[Dict[str, Any]]:
        """Collect a log entry from queue."""
        try:
            return await asyncio.wait_for(self._queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            return None
