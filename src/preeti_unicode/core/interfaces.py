"""
Interface definitions for the Preeti Unicode converter.

This module defines all the interfaces that components must implement
to ensure consistency and extensibility throughout the system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Generic, TypeVar, Protocol
from pathlib import Path
from enum import Enum

# Type variables for generic interfaces
T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')


class ProcessingStatus(Enum):
    """Status enumeration for processing operations."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class LogLevel(Enum):
    """Logging level enumeration."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class IConverter(ABC, Generic[T]):
    """Interface for text conversion operations."""
    
    @abstractmethod
    def convert(self, text: str, **kwargs) -> str:
        """
        Convert text from one format to another.
        
        Args:
            text: Input text to convert
            **kwargs: Additional conversion options
            
        Returns:
            Converted text
        """
        pass
    
    @abstractmethod
    def validate_input(self, text: str) -> bool:
        """
        Validate if the input text is suitable for conversion.
        
        Args:
            text: Text to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported input formats.
        
        Returns:
            List of supported format names
        """
        pass


class IReader(ABC, Generic[T]):
    """Interface for file reading operations."""
    
    @abstractmethod
    def read(self, file_path: Path, **kwargs) -> Dict[str, Any]:
        """
        Read content from a file.
        
        Args:
            file_path: Path to the file to read
            **kwargs: Additional reading options
            
        Returns:
            Dictionary containing extracted content and metadata
        """
        pass
    
    @abstractmethod
    def validate_file(self, file_path: Path) -> bool:
        """
        Validate if the file can be read by this reader.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            True if file is valid and readable, False otherwise
        """
        pass
    
    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """
        Get list of supported file extensions.
        
        Returns:
            List of supported file extensions (including the dot)
        """
        pass


class IWriter(ABC, Generic[T]):
    """Interface for file writing operations."""
    
    @abstractmethod
    def write(self, content: Dict[str, Any], file_path: Path, **kwargs) -> bool:
        """
        Write content to a file.
        
        Args:
            content: Content dictionary to write
            file_path: Path where to write the file
            **kwargs: Additional writing options
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported output formats.
        
        Returns:
            List of supported format names
        """
        pass


class IValidator(ABC):
    """Interface for validation operations."""
    
    @abstractmethod
    def validate(self, data: Any, **kwargs) -> bool:
        """
        Validate the given data.
        
        Args:
            data: Data to validate
            **kwargs: Additional validation options
            
        Returns:
            True if valid, False otherwise
        """
        pass
    
    @abstractmethod
    def get_validation_errors(self, data: Any, **kwargs) -> List[str]:
        """
        Get detailed validation errors for the given data.
        
        Args:
            data: Data to validate
            **kwargs: Additional validation options
            
        Returns:
            List of validation error messages
        """
        pass


class ICache(ABC, Generic[K, V]):
    """Interface for caching operations."""
    
    @abstractmethod
    def get(self, key: K) -> Optional[V]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        pass
    
    @abstractmethod
    def set(self, key: K, value: V, ttl: Optional[int] = None) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)
        """
        pass
    
    @abstractmethod
    def delete(self, key: K) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False if key not found
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all cached values."""
        pass


class ILogger(ABC):
    """Interface for logging operations."""
    
    @abstractmethod
    def log(self, level: LogLevel, message: str, **kwargs) -> None:
        """
        Log a message at the specified level.
        
        Args:
            level: Log level
            message: Message to log
            **kwargs: Additional context data
        """
        pass
    
    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        pass
    
    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        pass
    
    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        pass
    
    @abstractmethod
    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        pass
    
    @abstractmethod
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        pass


class IPlugin(ABC):
    """Interface for plugin components."""
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the plugin with configuration.
        
        Args:
            config: Plugin configuration dictionary
        """
        pass
    
    @abstractmethod
    def execute(self, data: Any, **kwargs) -> Any:
        """
        Execute the plugin's main functionality.
        
        Args:
            data: Input data
            **kwargs: Additional execution options
            
        Returns:
            Processed data
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """
        Get the plugin name.
        
        Returns:
            Plugin name
        """
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """
        Get the plugin version.
        
        Returns:
            Plugin version string
        """
        pass


class IMiddleware(ABC):
    """Interface for middleware components."""
    
    @abstractmethod
    def process_before(self, data: Any, **kwargs) -> Any:
        """
        Process data before main operation.
        
        Args:
            data: Input data
            **kwargs: Additional processing options
            
        Returns:
            Processed data
        """
        pass
    
    @abstractmethod
    def process_after(self, data: Any, **kwargs) -> Any:
        """
        Process data after main operation.
        
        Args:
            data: Output data from main operation
            **kwargs: Additional processing options
            
        Returns:
            Processed data
        """
        pass


class IProgressTracker(ABC):
    """Interface for progress tracking operations."""
    
    @abstractmethod
    def start(self, total: int, description: str = "") -> None:
        """
        Start progress tracking.
        
        Args:
            total: Total number of items to process
            description: Description of the operation
        """
        pass
    
    @abstractmethod
    def update(self, current: int, message: str = "") -> None:
        """
        Update progress.
        
        Args:
            current: Current progress count
            message: Optional progress message
        """
        pass
    
    @abstractmethod
    def finish(self, message: str = "") -> None:
        """
        Finish progress tracking.
        
        Args:
            message: Optional completion message
        """
        pass
    
    @abstractmethod
    def get_status(self) -> ProcessingStatus:
        """
        Get current processing status.
        
        Returns:
            Current status
        """
        pass
