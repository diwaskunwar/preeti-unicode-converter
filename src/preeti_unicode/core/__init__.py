"""
Core module containing base classes, interfaces, and fundamental components.
"""

from .interfaces import (
    IConverter,
    IReader,
    IWriter,
    IValidator,
    ICache,
    ILogger,
    IPlugin,
    IMiddleware,
    IProgressTracker
)

from .exceptions import (
    PreetiUnicodeError,
    ConversionError,
    FileProcessingError,
    ValidationError,
    PluginError,
    CacheError
)

from .base_classes import (
    BaseConverter,
    BaseReader,
    BaseWriter,
    BaseValidator,
    BasePlugin,
    BaseMiddleware
)

from .factories import (
    ReaderFactory,
    WriterFactory,
    ConverterFactory,
    ValidatorFactory
)

from .config import (
    Configuration,
    LoggingConfig,
    CacheConfig,
    ProcessingConfig
)

__all__ = [
    # Interfaces
    'IConverter', 'IReader', 'IWriter', 'IValidator', 'ICache', 'ILogger',
    'IPlugin', 'IMiddleware', 'IProgressTracker',
    
    # Exceptions
    'PreetiUnicodeError', 'ConversionError', 'FileProcessingError',
    'ValidationError', 'PluginError', 'CacheError',
    
    # Base Classes
    'BaseConverter', 'BaseReader', 'BaseWriter', 'BaseValidator',
    'BasePlugin', 'BaseMiddleware',
    
    # Factories
    'ReaderFactory', 'WriterFactory', 'ConverterFactory', 'ValidatorFactory',
    
    # Configuration
    'Configuration', 'LoggingConfig', 'CacheConfig', 'ProcessingConfig'
]
