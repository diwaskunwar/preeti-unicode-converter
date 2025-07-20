"""
Custom exception classes for the Preeti Unicode converter.

This module defines a comprehensive hierarchy of exceptions that provide
detailed error information and enable graceful error handling throughout
the application.
"""

from typing import Any, Dict, List, Optional, Union
from pathlib import Path


class PreetiUnicodeError(Exception):
    """
    Base exception class for all Preeti Unicode converter errors.
    
    This is the root exception that all other custom exceptions inherit from.
    It provides common functionality for error handling and reporting.
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        """
        Initialize the exception.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error details
            cause: Original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.cause = cause
    
    def __str__(self) -> str:
        """Return string representation of the error."""
        result = f"{self.error_code}: {self.message}"
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            result += f" ({details_str})"
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary format.
        
        Returns:
            Dictionary representation of the exception
        """
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "type": self.__class__.__name__,
            "cause": str(self.cause) if self.cause else None
        }


class ConversionError(PreetiUnicodeError):
    """
    Exception raised when text conversion fails.
    
    This exception is raised when the conversion process encounters
    an error that prevents successful text transformation.
    """
    
    def __init__(
        self,
        message: str,
        input_text: Optional[str] = None,
        conversion_type: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize conversion error.
        
        Args:
            message: Error message
            input_text: The text that failed to convert
            conversion_type: Type of conversion that failed
            **kwargs: Additional arguments for base class
        """
        details = kwargs.get('details', {})
        if input_text is not None:
            details['input_text'] = input_text[:100] + "..." if len(input_text) > 100 else input_text
        if conversion_type is not None:
            details['conversion_type'] = conversion_type
        
        kwargs['details'] = details
        super().__init__(message, **kwargs)


class FileProcessingError(PreetiUnicodeError):
    """
    Exception raised when file processing operations fail.
    
    This includes errors in reading, writing, or validating files.
    """
    
    def __init__(
        self,
        message: str,
        file_path: Optional[Union[str, Path]] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize file processing error.
        
        Args:
            message: Error message
            file_path: Path to the file that caused the error
            operation: The operation that failed (read, write, validate, etc.)
            **kwargs: Additional arguments for base class
        """
        details = kwargs.get('details', {})
        if file_path is not None:
            details['file_path'] = str(file_path)
        if operation is not None:
            details['operation'] = operation
        
        kwargs['details'] = details
        super().__init__(message, **kwargs)


class ValidationError(PreetiUnicodeError):
    """
    Exception raised when validation fails.
    
    This exception is raised when input validation or file validation
    encounters errors that prevent processing.
    """
    
    def __init__(
        self,
        message: str,
        validation_errors: Optional[List[str]] = None,
        field_name: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            validation_errors: List of specific validation errors
            field_name: Name of the field that failed validation
            **kwargs: Additional arguments for base class
        """
        details = kwargs.get('details', {})
        if validation_errors is not None:
            details['validation_errors'] = validation_errors
        if field_name is not None:
            details['field_name'] = field_name
        
        kwargs['details'] = details
        super().__init__(message, **kwargs)


class PluginError(PreetiUnicodeError):
    """
    Exception raised when plugin operations fail.
    
    This includes errors in plugin loading, initialization, or execution.
    """
    
    def __init__(
        self,
        message: str,
        plugin_name: Optional[str] = None,
        plugin_version: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize plugin error.
        
        Args:
            message: Error message
            plugin_name: Name of the plugin that caused the error
            plugin_version: Version of the plugin
            **kwargs: Additional arguments for base class
        """
        details = kwargs.get('details', {})
        if plugin_name is not None:
            details['plugin_name'] = plugin_name
        if plugin_version is not None:
            details['plugin_version'] = plugin_version
        
        kwargs['details'] = details
        super().__init__(message, **kwargs)


class CacheError(PreetiUnicodeError):
    """
    Exception raised when cache operations fail.
    
    This includes errors in cache access, storage, or retrieval.
    """
    
    def __init__(
        self,
        message: str,
        cache_key: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize cache error.
        
        Args:
            message: Error message
            cache_key: The cache key that caused the error
            operation: The cache operation that failed
            **kwargs: Additional arguments for base class
        """
        details = kwargs.get('details', {})
        if cache_key is not None:
            details['cache_key'] = str(cache_key)
        if operation is not None:
            details['operation'] = operation
        
        kwargs['details'] = details
        super().__init__(message, **kwargs)


class ConfigurationError(PreetiUnicodeError):
    """
    Exception raised when configuration is invalid or missing.
    
    This exception is raised when the application configuration
    contains invalid values or required settings are missing.
    """
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        expected_type: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize configuration error.
        
        Args:
            message: Error message
            config_key: The configuration key that caused the error
            expected_type: The expected type for the configuration value
            **kwargs: Additional arguments for base class
        """
        details = kwargs.get('details', {})
        if config_key is not None:
            details['config_key'] = config_key
        if expected_type is not None:
            details['expected_type'] = expected_type
        
        kwargs['details'] = details
        super().__init__(message, **kwargs)


class DependencyError(PreetiUnicodeError):
    """
    Exception raised when required dependencies are missing or incompatible.
    
    This exception is raised when optional or required dependencies
    are not available or have incompatible versions.
    """
    
    def __init__(
        self,
        message: str,
        dependency_name: Optional[str] = None,
        required_version: Optional[str] = None,
        available_version: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize dependency error.
        
        Args:
            message: Error message
            dependency_name: Name of the missing or incompatible dependency
            required_version: Required version of the dependency
            available_version: Available version of the dependency
            **kwargs: Additional arguments for base class
        """
        details = kwargs.get('details', {})
        if dependency_name is not None:
            details['dependency_name'] = dependency_name
        if required_version is not None:
            details['required_version'] = required_version
        if available_version is not None:
            details['available_version'] = available_version
        
        kwargs['details'] = details
        super().__init__(message, **kwargs)


class ProcessingTimeoutError(PreetiUnicodeError):
    """
    Exception raised when processing operations timeout.
    
    This exception is raised when operations take longer than
    the configured timeout period.
    """
    
    def __init__(
        self,
        message: str,
        timeout_seconds: Optional[float] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize processing timeout error.
        
        Args:
            message: Error message
            timeout_seconds: The timeout period that was exceeded
            operation: The operation that timed out
            **kwargs: Additional arguments for base class
        """
        details = kwargs.get('details', {})
        if timeout_seconds is not None:
            details['timeout_seconds'] = timeout_seconds
        if operation is not None:
            details['operation'] = operation
        
        kwargs['details'] = details
        super().__init__(message, **kwargs)
