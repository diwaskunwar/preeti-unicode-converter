"""
Base classes implementing common functionality for the Preeti Unicode converter.

This module provides abstract base classes that implement common patterns
and provide default implementations for interface methods.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Generic, TypeVar
from pathlib import Path
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from preeti_unicode.core.interfaces import (
    IConverter, IReader, IWriter, IValidator, IPlugin, IMiddleware,
    IProgressTracker, ProcessingStatus, LogLevel
)
from preeti_unicode.core.exceptions import (
    PreetiUnicodeError, ConversionError, FileProcessingError,
    ValidationError, PluginError, ProcessingTimeoutError
)

T = TypeVar('T')


class BaseConverter(IConverter[T], ABC):
    """
    Base implementation for text converters.
    
    Provides common functionality for conversion operations including
    validation, error handling, and logging.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the base converter.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self._supported_formats: List[str] = []
    
    def convert(self, text: str, **kwargs) -> str:
        """
        Convert text with validation and error handling.
        
        Args:
            text: Input text to convert
            **kwargs: Additional conversion options
            
        Returns:
            Converted text
            
        Raises:
            ConversionError: If conversion fails
            ValidationError: If input validation fails
        """
        try:
            # Validate input
            if not self.validate_input(text):
                raise ValidationError(
                    "Input text validation failed",
                    field_name="text"
                )
            
            # Perform conversion
            self.logger.debug(f"Converting text of length {len(text)}")
            start_time = time.time()
            
            result = self._convert_impl(text, **kwargs)
            
            elapsed_time = time.time() - start_time
            self.logger.debug(f"Conversion completed in {elapsed_time:.3f} seconds")
            
            return result
            
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Conversion failed: {e}")
            raise ConversionError(
                f"Failed to convert text: {str(e)}",
                input_text=text,
                conversion_type=self.__class__.__name__,
                cause=e
            )
    
    @abstractmethod
    def _convert_impl(self, text: str, **kwargs) -> str:
        """
        Implement the actual conversion logic.
        
        Args:
            text: Input text to convert
            **kwargs: Additional conversion options
            
        Returns:
            Converted text
        """
        pass
    
    def validate_input(self, text: str) -> bool:
        """
        Default input validation.
        
        Args:
            text: Text to validate
            
        Returns:
            True if valid, False otherwise
        """
        return text is not None and isinstance(text, str)
    
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported input formats.
        
        Returns:
            List of supported format names
        """
        return self._supported_formats.copy()


class BaseReader(IReader[T], ABC):
    """
    Base implementation for file readers.
    
    Provides common functionality for file reading operations including
    validation, error handling, and progress tracking.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the base reader.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self._supported_extensions: List[str] = []
    
    def read(self, file_path: Path, **kwargs) -> Dict[str, Any]:
        """
        Read file with validation and error handling.
        
        Args:
            file_path: Path to the file to read
            **kwargs: Additional reading options
            
        Returns:
            Dictionary containing extracted content and metadata
            
        Raises:
            FileProcessingError: If file reading fails
            ValidationError: If file validation fails
        """
        try:
            # Validate file
            if not self.validate_file(file_path):
                raise ValidationError(
                    f"File validation failed: {file_path}",
                    field_name="file_path"
                )
            
            # Read file
            self.logger.debug(f"Reading file: {file_path}")
            start_time = time.time()
            
            result = self._read_impl(file_path, **kwargs)
            
            elapsed_time = time.time() - start_time
            self.logger.debug(f"File read completed in {elapsed_time:.3f} seconds")
            
            # Add metadata
            result.setdefault('metadata', {}).update({
                'file_path': str(file_path),
                'file_size': file_path.stat().st_size if file_path.exists() else 0,
                'read_time': elapsed_time,
                'reader_type': self.__class__.__name__
            })
            
            return result
            
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to read file {file_path}: {e}")
            raise FileProcessingError(
                f"Failed to read file: {str(e)}",
                file_path=file_path,
                operation="read",
                cause=e
            )
    
    @abstractmethod
    def _read_impl(self, file_path: Path, **kwargs) -> Dict[str, Any]:
        """
        Implement the actual file reading logic.
        
        Args:
            file_path: Path to the file to read
            **kwargs: Additional reading options
            
        Returns:
            Dictionary containing extracted content and metadata
        """
        pass
    
    def validate_file(self, file_path: Path) -> bool:
        """
        Default file validation.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            True if file is valid and readable, False otherwise
        """
        if not file_path.exists():
            return False
        
        if not file_path.is_file():
            return False
        
        # Check file extension
        if self._supported_extensions:
            return file_path.suffix.lower() in self._supported_extensions
        
        return True
    
    def get_supported_extensions(self) -> List[str]:
        """
        Get list of supported file extensions.
        
        Returns:
            List of supported file extensions (including the dot)
        """
        return self._supported_extensions.copy()


class BaseWriter(IWriter[T], ABC):
    """
    Base implementation for file writers.
    
    Provides common functionality for file writing operations including
    error handling and directory creation.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the base writer.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self._supported_formats: List[str] = []
    
    def write(self, content: Dict[str, Any], file_path: Path, **kwargs) -> bool:
        """
        Write content to file with error handling.
        
        Args:
            content: Content dictionary to write
            file_path: Path where to write the file
            **kwargs: Additional writing options
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            FileProcessingError: If file writing fails
        """
        try:
            # Ensure output directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            self.logger.debug(f"Writing file: {file_path}")
            start_time = time.time()
            
            result = self._write_impl(content, file_path, **kwargs)
            
            elapsed_time = time.time() - start_time
            self.logger.debug(f"File write completed in {elapsed_time:.3f} seconds")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to write file {file_path}: {e}")
            raise FileProcessingError(
                f"Failed to write file: {str(e)}",
                file_path=file_path,
                operation="write",
                cause=e
            )
    
    @abstractmethod
    def _write_impl(self, content: Dict[str, Any], file_path: Path, **kwargs) -> bool:
        """
        Implement the actual file writing logic.
        
        Args:
            content: Content dictionary to write
            file_path: Path where to write the file
            **kwargs: Additional writing options
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported output formats.
        
        Returns:
            List of supported format names
        """
        return self._supported_formats.copy()


class BaseValidator(IValidator, ABC):
    """
    Base implementation for validators.
    
    Provides common functionality for validation operations.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the base validator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(self.__class__.__name__)
    
    def validate(self, data: Any, **kwargs) -> bool:
        """
        Validate data and return boolean result.
        
        Args:
            data: Data to validate
            **kwargs: Additional validation options
            
        Returns:
            True if valid, False otherwise
        """
        errors = self.get_validation_errors(data, **kwargs)
        return len(errors) == 0
    
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


class BasePlugin(IPlugin, ABC):
    """
    Base implementation for plugins.
    
    Provides common functionality for plugin operations.
    """
    
    def __init__(self, name: str, version: str, logger: Optional[logging.Logger] = None):
        """
        Initialize the base plugin.
        
        Args:
            name: Plugin name
            version: Plugin version
            logger: Optional logger instance
        """
        self._name = name
        self._version = version
        self.logger = logger or logging.getLogger(f"Plugin.{name}")
        self._initialized = False
        self._config: Dict[str, Any] = {}
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the plugin with configuration.
        
        Args:
            config: Plugin configuration dictionary
            
        Raises:
            PluginError: If initialization fails
        """
        try:
            self.logger.debug(f"Initializing plugin {self._name}")
            self._config = config.copy()
            self._initialize_impl(config)
            self._initialized = True
            self.logger.info(f"Plugin {self._name} initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize plugin {self._name}: {e}")
            raise PluginError(
                f"Plugin initialization failed: {str(e)}",
                plugin_name=self._name,
                plugin_version=self._version,
                cause=e
            )
    
    @abstractmethod
    def _initialize_impl(self, config: Dict[str, Any]) -> None:
        """
        Implement plugin-specific initialization logic.
        
        Args:
            config: Plugin configuration dictionary
        """
        pass
    
    def execute(self, data: Any, **kwargs) -> Any:
        """
        Execute the plugin's main functionality.
        
        Args:
            data: Input data
            **kwargs: Additional execution options
            
        Returns:
            Processed data
            
        Raises:
            PluginError: If execution fails
        """
        if not self._initialized:
            raise PluginError(
                "Plugin not initialized",
                plugin_name=self._name,
                plugin_version=self._version
            )
        
        try:
            self.logger.debug(f"Executing plugin {self._name}")
            return self._execute_impl(data, **kwargs)
            
        except Exception as e:
            self.logger.error(f"Plugin {self._name} execution failed: {e}")
            raise PluginError(
                f"Plugin execution failed: {str(e)}",
                plugin_name=self._name,
                plugin_version=self._version,
                cause=e
            )
    
    @abstractmethod
    def _execute_impl(self, data: Any, **kwargs) -> Any:
        """
        Implement plugin-specific execution logic.
        
        Args:
            data: Input data
            **kwargs: Additional execution options
            
        Returns:
            Processed data
        """
        pass
    
    def get_name(self) -> str:
        """
        Get the plugin name.
        
        Returns:
            Plugin name
        """
        return self._name
    
    def get_version(self) -> str:
        """
        Get the plugin version.
        
        Returns:
            Plugin version string
        """
        return self._version


class BaseMiddleware(IMiddleware, ABC):
    """
    Base implementation for middleware components.
    
    Provides common functionality for middleware operations.
    """
    
    def __init__(self, name: str, logger: Optional[logging.Logger] = None):
        """
        Initialize the base middleware.
        
        Args:
            name: Middleware name
            logger: Optional logger instance
        """
        self._name = name
        self.logger = logger or logging.getLogger(f"Middleware.{name}")
    
    def process_before(self, data: Any, **kwargs) -> Any:
        """
        Process data before main operation with error handling.
        
        Args:
            data: Input data
            **kwargs: Additional processing options
            
        Returns:
            Processed data
        """
        try:
            self.logger.debug(f"Processing before with middleware {self._name}")
            return self._process_before_impl(data, **kwargs)
        except Exception as e:
            self.logger.error(f"Middleware {self._name} before processing failed: {e}")
            raise
    
    def process_after(self, data: Any, **kwargs) -> Any:
        """
        Process data after main operation with error handling.
        
        Args:
            data: Output data from main operation
            **kwargs: Additional processing options
            
        Returns:
            Processed data
        """
        try:
            self.logger.debug(f"Processing after with middleware {self._name}")
            return self._process_after_impl(data, **kwargs)
        except Exception as e:
            self.logger.error(f"Middleware {self._name} after processing failed: {e}")
            raise
    
    def _process_before_impl(self, data: Any, **kwargs) -> Any:
        """
        Default implementation for before processing.
        
        Args:
            data: Input data
            **kwargs: Additional processing options
            
        Returns:
            Unmodified data (default behavior)
        """
        return data
    
    def _process_after_impl(self, data: Any, **kwargs) -> Any:
        """
        Default implementation for after processing.
        
        Args:
            data: Output data from main operation
            **kwargs: Additional processing options
            
        Returns:
            Unmodified data (default behavior)
        """
        return data
