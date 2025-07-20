"""
Advanced logging system with structured logging and multiple handlers.

This module provides comprehensive logging capabilities including
structured logging, multiple output formats, and performance monitoring.
"""

import logging
import logging.handlers
import json
import time
import threading
from typing import Any, Dict, Optional, List, Union
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from contextlib import contextmanager

from preeti_unicode.core.interfaces import ILogger, LogLevel
from preeti_unicode.core.config import LoggingConfig


@dataclass
class LogEntry:
    """Structured log entry with metadata."""
    timestamp: str
    level: str
    logger_name: str
    message: str
    module: Optional[str] = None
    function: Optional[str] = None
    line_number: Optional[int] = None
    thread_id: Optional[int] = None
    process_id: Optional[int] = None
    extra_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON format."""
        return json.dumps(self.to_dict(), default=str)


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter for structured logging.
    
    Formats log records as structured data (JSON) with
    additional metadata and context information.
    """
    
    def __init__(self, include_extra: bool = True):
        """
        Initialize the structured formatter.
        
        Args:
            include_extra: Whether to include extra fields in output
        """
        super().__init__()
        self.include_extra = include_extra
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record as structured JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted log entry as JSON string
        """
        # Extract extra data
        extra_data = {}
        if self.include_extra:
            # Get all extra attributes from the record
            for key, value in record.__dict__.items():
                if key not in {
                    'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                    'filename', 'module', 'lineno', 'funcName', 'created',
                    'msecs', 'relativeCreated', 'thread', 'threadName',
                    'processName', 'process', 'getMessage', 'exc_info',
                    'exc_text', 'stack_info'
                }:
                    extra_data[key] = value
        
        # Create structured log entry
        log_entry = LogEntry(
            timestamp=datetime.fromtimestamp(record.created).isoformat(),
            level=record.levelname,
            logger_name=record.name,
            message=record.getMessage(),
            module=record.module,
            function=record.funcName,
            line_number=record.lineno,
            thread_id=record.thread,
            process_id=record.process,
            extra_data=extra_data if extra_data else None
        )
        
        return log_entry.to_json()


class PerformanceLogger:
    """
    Logger for performance monitoring and timing.
    
    Provides utilities for measuring and logging
    execution times and performance metrics.
    """
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize the performance logger.
        
        Args:
            logger: Base logger to use for output
        """
        self.logger = logger
        self._timers: Dict[str, float] = {}
        self._lock = threading.RLock()
    
    @contextmanager
    def timer(self, operation_name: str, **extra_data):
        """
        Context manager for timing operations.
        
        Args:
            operation_name: Name of the operation being timed
            **extra_data: Additional data to include in log
        """
        start_time = time.time()
        
        try:
            yield
        finally:
            execution_time = time.time() - start_time
            self.log_timing(operation_name, execution_time, **extra_data)
    
    def start_timer(self, timer_name: str) -> None:
        """
        Start a named timer.
        
        Args:
            timer_name: Name of the timer
        """
        with self._lock:
            self._timers[timer_name] = time.time()
    
    def stop_timer(self, timer_name: str, **extra_data) -> float:
        """
        Stop a named timer and log the result.
        
        Args:
            timer_name: Name of the timer
            **extra_data: Additional data to include in log
            
        Returns:
            Execution time in seconds
        """
        with self._lock:
            if timer_name not in self._timers:
                self.logger.warning(f"Timer {timer_name} was not started")
                return 0.0
            
            start_time = self._timers.pop(timer_name)
            execution_time = time.time() - start_time
            
            self.log_timing(timer_name, execution_time, **extra_data)
            return execution_time
    
    def log_timing(self, operation_name: str, execution_time: float, **extra_data) -> None:
        """
        Log timing information.
        
        Args:
            operation_name: Name of the operation
            execution_time: Execution time in seconds
            **extra_data: Additional data to include
        """
        self.logger.info(
            f"Performance: {operation_name} completed in {execution_time:.3f}s",
            extra={
                'operation': operation_name,
                'execution_time': execution_time,
                'performance_log': True,
                **extra_data
            }
        )


class StructuredLogger(ILogger):
    """
    Structured logger implementation with enhanced features.
    
    Provides structured logging with performance monitoring,
    context management, and flexible output formats.
    """
    
    def __init__(
        self,
        name: str,
        config: Optional[LoggingConfig] = None,
        structured: bool = True
    ):
        """
        Initialize the structured logger.
        
        Args:
            name: Logger name
            config: Logging configuration
            structured: Whether to use structured logging format
        """
        self.name = name
        self.config = config or LoggingConfig()
        self.structured = structured
        
        # Create base logger
        self._logger = logging.getLogger(name)
        self._logger.setLevel(getattr(logging, self.config.level.value))
        
        # Clear existing handlers
        self._logger.handlers.clear()
        
        # Setup handlers
        self._setup_handlers()
        
        # Create performance logger
        self.performance = PerformanceLogger(self._logger)
        
        # Context storage
        self._context: Dict[str, Any] = {}
        self._context_lock = threading.RLock()
    
    def _setup_handlers(self) -> None:
        """Setup log handlers based on configuration."""
        # Console handler
        if self.config.console_output:
            console_handler = logging.StreamHandler()
            
            if self.structured:
                console_handler.setFormatter(StructuredFormatter())
            else:
                console_handler.setFormatter(logging.Formatter(self.config.format))
            
            self._logger.addHandler(console_handler)
        
        # File handler
        if self.config.file_path:
            # Ensure directory exists
            self.config.file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Use rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                filename=self.config.file_path,
                maxBytes=self.config.max_file_size,
                backupCount=self.config.backup_count,
                encoding='utf-8'
            )
            
            if self.structured:
                file_handler.setFormatter(StructuredFormatter())
            else:
                file_handler.setFormatter(logging.Formatter(self.config.format))
            
            self._logger.addHandler(file_handler)
    
    def set_context(self, **context_data) -> None:
        """
        Set context data that will be included in all log entries.
        
        Args:
            **context_data: Context data to set
        """
        with self._context_lock:
            self._context.update(context_data)
    
    def clear_context(self) -> None:
        """Clear all context data."""
        with self._context_lock:
            self._context.clear()
    
    @contextmanager
    def context(self, **context_data):
        """
        Context manager for temporary context data.
        
        Args:
            **context_data: Temporary context data
        """
        # Save current context
        with self._context_lock:
            old_context = self._context.copy()
            self._context.update(context_data)
        
        try:
            yield
        finally:
            # Restore old context
            with self._context_lock:
                self._context = old_context
    
    def log(self, level: LogLevel, message: str, **kwargs) -> None:
        """
        Log a message at the specified level.
        
        Args:
            level: Log level
            message: Message to log
            **kwargs: Additional context data
        """
        # Combine context and kwargs
        with self._context_lock:
            extra_data = {**self._context, **kwargs}
        
        # Map LogLevel to logging level
        log_level = getattr(logging, level.value)
        
        self._logger.log(log_level, message, extra=extra_data)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self.log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self.log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self.log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self.log(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        self.log(LogLevel.CRITICAL, message, **kwargs)


class LoggingManager:
    """
    Manager for multiple logger instances.
    
    Provides centralized management of loggers with
    configuration and lifecycle management.
    """
    
    def __init__(self, config: Optional[LoggingConfig] = None):
        """
        Initialize the logging manager.
        
        Args:
            config: Default logging configuration
        """
        self.config = config or LoggingConfig()
        self._loggers: Dict[str, StructuredLogger] = {}
        self._lock = threading.RLock()
    
    def get_logger(
        self,
        name: str,
        config: Optional[LoggingConfig] = None,
        structured: bool = True
    ) -> StructuredLogger:
        """
        Get or create a logger instance.
        
        Args:
            name: Logger name
            config: Optional logger-specific configuration
            structured: Whether to use structured logging
            
        Returns:
            Logger instance
        """
        with self._lock:
            if name not in self._loggers:
                logger_config = config or self.config
                self._loggers[name] = StructuredLogger(name, logger_config, structured)
            
            return self._loggers[name]
    
    def configure_all_loggers(self, config: LoggingConfig) -> None:
        """
        Update configuration for all existing loggers.
        
        Args:
            config: New logging configuration
        """
        with self._lock:
            self.config = config
            
            # Recreate all loggers with new configuration
            for name in list(self._loggers.keys()):
                structured = self._loggers[name].structured
                self._loggers[name] = StructuredLogger(name, config, structured)
    
    def shutdown(self) -> None:
        """Shutdown all loggers and handlers."""
        with self._lock:
            for logger in self._loggers.values():
                for handler in logger._logger.handlers:
                    handler.close()
                logger._logger.handlers.clear()
            
            self._loggers.clear()


# Global logging manager
_logging_manager = LoggingManager()


def setup_logging(config: LoggingConfig) -> None:
    """
    Setup global logging configuration.
    
    Args:
        config: Logging configuration
    """
    _logging_manager.configure_all_loggers(config)


def get_logger(
    name: str,
    config: Optional[LoggingConfig] = None,
    structured: bool = True
) -> StructuredLogger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name
        config: Optional logger-specific configuration
        structured: Whether to use structured logging
        
    Returns:
        Logger instance
    """
    return _logging_manager.get_logger(name, config, structured)


def shutdown_logging() -> None:
    """Shutdown all logging."""
    _logging_manager.shutdown()
