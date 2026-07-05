"""Structured logging service."""

import logging
import logging.handlers
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import time
import threading

from config.system_config import config, LogLevel


class DuplicateFilter(logging.Filter):
    """Filters out duplicate log messages within a cooldown period (low RAM friendly)."""
    
    def __init__(self, cooldown_seconds: float = 5.0):
        super().__init__()
        self.cooldown = cooldown_seconds
        self.last_logs = {}  # (module, msg, args_str) -> last_time
        self.lock = threading.Lock()
        
    def filter(self, record: logging.LogRecord) -> bool:
        now = time.time()
        key = (record.name, record.msg, str(record.args))
        
        with self.lock:
            # Clean up old keys
            self.last_logs = {k: t for k, t in self.last_logs.items() if now - t < self.cooldown}
            
            last_time = self.last_logs.get(key)
            if last_time and (now - last_time) < self.cooldown:
                return False
            
            self.last_logs[key] = now
            return True


class LogEntry:
    """Represents a single log entry."""
    
    def __init__(self, timestamp: datetime, level: str, module: str, message: str):
        self.timestamp = timestamp
        self.level = level
        self.module = module
        self.message = message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "module": self.module,
            "message": self.message
        }


class RingBuffer(logging.Handler):
    """In-memory ring buffer for recent logs (low RAM friendly)."""
    
    def __init__(self, capacity: int = 100):
        super().__init__()
        self.buffer: deque = deque(maxlen=capacity)
    
    def emit(self, record: logging.LogRecord) -> None:
        """Add log record to buffer."""
        entry = LogEntry(
            timestamp=datetime.fromtimestamp(record.created),
            level=record.levelname,
            module=record.name,
            message=record.getMessage()
        )
        self.buffer.append(entry)
    
    def get_logs(self) -> List[Dict[str, Any]]:
        """Get all logs as dictionaries."""
        return [entry.to_dict() for entry in self.buffer]
    
    def clear(self) -> None:
        """Clear all logs."""
        self.buffer.clear()


class LoggerService:
    """Centralized logging service."""
    
    _instance = None
    _ring_buffer = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        
        self._initialized = True
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Configure logging system."""
        logger = logging.getLogger("opencvdash")
        logger.setLevel(getattr(logging, config.LOG_LEVEL.value))
        
        # Add duplicate filter to throttle repetitive logs
        dup_filter = DuplicateFilter(cooldown_seconds=5.0)
        logger.addFilter(dup_filter)
        
        # Remove existing handlers
        logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, config.LOG_LEVEL.value))
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler
        log_file = config.LOGS_DIR / "application.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=5_000_000,  # 5MB
            backupCount=3
        )
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Ring buffer for UI (low RAM)
        LoggerService._ring_buffer = RingBuffer(capacity=config.MAX_LOG_ENTRIES)
        logger.addHandler(LoggerService._ring_buffer)
        
        self.logger = logger
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get named logger."""
        return logging.getLogger(f"opencvdash.{name}")
    
    def get_recent_logs(self) -> List[Dict[str, Any]]:
        """Get recent logs from ring buffer."""
        if LoggerService._ring_buffer:
            return LoggerService._ring_buffer.get_logs()
        return []
    
    def log_event(self, level: str, module: str, message: str) -> None:
        """Log an event."""
        logger = self.get_logger(module)
        log_method = getattr(logger, level.lower(), logger.info)
        log_method(message)


# Global logger instance
logger_service = LoggerService()
