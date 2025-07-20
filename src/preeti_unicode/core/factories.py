"""
Factory classes for creating instances of readers, writers, converters, and validators.

This module implements the Factory pattern to provide a centralized way
to create instances of various components based on configuration or type.
"""

from typing import Dict, Type, Optional, Any, List
from pathlib import Path
import logging

from preeti_unicode.core.interfaces import IReader, IWriter, IConverter, IValidator
from preeti_unicode.core.exceptions import ConfigurationError, DependencyError


class ComponentRegistry:
    """
    Registry for managing component types and their factories.
    
    This class provides a centralized registry for different component types
    and enables dynamic registration and creation of components.
    """
    
    def __init__(self):
        """Initialize the component registry."""
        self._components: Dict[str, Dict[str, Type]] = {
            'readers': {},
            'writers': {},
            'converters': {},
            'validators': {}
        }
        self._aliases: Dict[str, Dict[str, str]] = {
            'readers': {},
            'writers': {},
            'converters': {},
            'validators': {}
        }
    
    def register_reader(self, name: str, reader_class: Type[IReader], aliases: Optional[List[str]] = None) -> None:
        """
        Register a reader class.
        
        Args:
            name: Name of the reader
            reader_class: Reader class to register
            aliases: Optional list of aliases for the reader
        """
        self._components['readers'][name] = reader_class
        if aliases:
            for alias in aliases:
                self._aliases['readers'][alias] = name
    
    def register_writer(self, name: str, writer_class: Type[IWriter], aliases: Optional[List[str]] = None) -> None:
        """
        Register a writer class.
        
        Args:
            name: Name of the writer
            writer_class: Writer class to register
            aliases: Optional list of aliases for the writer
        """
        self._components['writers'][name] = writer_class
        if aliases:
            for alias in aliases:
                self._aliases['writers'][alias] = name
    
    def register_converter(self, name: str, converter_class: Type[IConverter], aliases: Optional[List[str]] = None) -> None:
        """
        Register a converter class.
        
        Args:
            name: Name of the converter
            converter_class: Converter class to register
            aliases: Optional list of aliases for the converter
        """
        self._components['converters'][name] = converter_class
        if aliases:
            for alias in aliases:
                self._aliases['converters'][alias] = name
    
    def register_validator(self, name: str, validator_class: Type[IValidator], aliases: Optional[List[str]] = None) -> None:
        """
        Register a validator class.
        
        Args:
            name: Name of the validator
            validator_class: Validator class to register
            aliases: Optional list of aliases for the validator
        """
        self._components['validators'][name] = validator_class
        if aliases:
            for alias in aliases:
                self._aliases['validators'][alias] = name
    
    def get_component_class(self, component_type: str, name: str) -> Type:
        """
        Get a component class by type and name.
        
        Args:
            component_type: Type of component ('readers', 'writers', etc.)
            name: Name or alias of the component
            
        Returns:
            Component class
            
        Raises:
            ConfigurationError: If component is not found
        """
        # Check if it's an alias
        if name in self._aliases.get(component_type, {}):
            name = self._aliases[component_type][name]
        
        # Get the component class
        if component_type not in self._components:
            raise ConfigurationError(f"Unknown component type: {component_type}")
        
        if name not in self._components[component_type]:
            available = list(self._components[component_type].keys())
            raise ConfigurationError(
                f"Unknown {component_type[:-1]}: {name}. Available: {available}"
            )
        
        return self._components[component_type][name]
    
    def list_components(self, component_type: str) -> List[str]:
        """
        List all registered components of a given type.
        
        Args:
            component_type: Type of component to list
            
        Returns:
            List of component names
        """
        return list(self._components.get(component_type, {}).keys())


# Global component registry
_registry = ComponentRegistry()


class BaseFactory:
    """
    Base factory class providing common functionality.
    
    This class provides common patterns for factory implementations
    including error handling and logging.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the base factory.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.registry = _registry
    
    def _create_instance(self, component_type: str, name: str, *args, **kwargs):
        """
        Create an instance of a component.
        
        Args:
            component_type: Type of component to create
            name: Name of the component
            *args: Positional arguments for the component constructor
            **kwargs: Keyword arguments for the component constructor
            
        Returns:
            Component instance
            
        Raises:
            ConfigurationError: If component creation fails
        """
        try:
            component_class = self.registry.get_component_class(component_type, name)
            self.logger.debug(f"Creating {component_type[:-1]} instance: {name}")
            return component_class(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Failed to create {component_type[:-1]} {name}: {e}")
            raise ConfigurationError(
                f"Failed to create {component_type[:-1]} {name}: {str(e)}",
                config_key=name,
                cause=e
            )


class ReaderFactory(BaseFactory):
    """
    Factory for creating file reader instances.
    
    This factory creates appropriate reader instances based on file type
    or explicit reader specification.
    """
    
    def create_reader(self, reader_type: Optional[str] = None, file_path: Optional[Path] = None, **kwargs) -> IReader:
        """
        Create a reader instance.
        
        Args:
            reader_type: Explicit reader type (optional)
            file_path: File path for auto-detection (optional)
            **kwargs: Additional arguments for the reader constructor
            
        Returns:
            Reader instance
            
        Raises:
            ConfigurationError: If reader cannot be determined or created
        """
        if reader_type is None and file_path is None:
            raise ConfigurationError("Either reader_type or file_path must be provided")
        
        # Auto-detect reader type from file extension
        if reader_type is None:
            reader_type = self._detect_reader_type(file_path)
        
        return self._create_instance('readers', reader_type, **kwargs)
    
    def _detect_reader_type(self, file_path: Path) -> str:
        """
        Detect reader type from file extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Reader type name
            
        Raises:
            ConfigurationError: If file type is not supported
        """
        extension = file_path.suffix.lower()
        
        # Extension to reader type mapping
        extension_map = {
            '.pdf': 'pdf',
            '.docx': 'docx',
            '.doc': 'docx',
            '.txt': 'txt',
            '.text': 'txt'
        }
        
        if extension not in extension_map:
            raise ConfigurationError(
                f"Unsupported file extension: {extension}",
                config_key="file_extension"
            )
        
        return extension_map[extension]
    
    def list_available_readers(self) -> List[str]:
        """
        List all available reader types.
        
        Returns:
            List of reader type names
        """
        return self.registry.list_components('readers')


class WriterFactory(BaseFactory):
    """
    Factory for creating file writer instances.
    
    This factory creates appropriate writer instances based on output format.
    """
    
    def create_writer(self, writer_type: str, **kwargs) -> IWriter:
        """
        Create a writer instance.
        
        Args:
            writer_type: Type of writer to create
            **kwargs: Additional arguments for the writer constructor
            
        Returns:
            Writer instance
        """
        return self._create_instance('writers', writer_type, **kwargs)
    
    def list_available_writers(self) -> List[str]:
        """
        List all available writer types.
        
        Returns:
            List of writer type names
        """
        return self.registry.list_components('writers')


class ConverterFactory(BaseFactory):
    """
    Factory for creating converter instances.
    
    This factory creates appropriate converter instances based on conversion type.
    """
    
    def create_converter(self, converter_type: str, **kwargs) -> IConverter:
        """
        Create a converter instance.
        
        Args:
            converter_type: Type of converter to create
            **kwargs: Additional arguments for the converter constructor
            
        Returns:
            Converter instance
        """
        return self._create_instance('converters', converter_type, **kwargs)
    
    def list_available_converters(self) -> List[str]:
        """
        List all available converter types.
        
        Returns:
            List of converter type names
        """
        return self.registry.list_components('converters')


class ValidatorFactory(BaseFactory):
    """
    Factory for creating validator instances.
    
    This factory creates appropriate validator instances based on validation type.
    """
    
    def create_validator(self, validator_type: str, **kwargs) -> IValidator:
        """
        Create a validator instance.
        
        Args:
            validator_type: Type of validator to create
            **kwargs: Additional arguments for the validator constructor
            
        Returns:
            Validator instance
        """
        return self._create_instance('validators', validator_type, **kwargs)
    
    def list_available_validators(self) -> List[str]:
        """
        List all available validator types.
        
        Returns:
            List of validator type names
        """
        return self.registry.list_components('validators')


# Global factory instances
reader_factory = ReaderFactory()
writer_factory = WriterFactory()
converter_factory = ConverterFactory()
validator_factory = ValidatorFactory()


def register_component(component_type: str, name: str, component_class: Type, aliases: Optional[List[str]] = None) -> None:
    """
    Register a component with the global registry.
    
    Args:
        component_type: Type of component ('reader', 'writer', 'converter', 'validator')
        name: Name of the component
        component_class: Component class to register
        aliases: Optional list of aliases
    """
    if component_type == 'reader':
        _registry.register_reader(name, component_class, aliases)
    elif component_type == 'writer':
        _registry.register_writer(name, component_class, aliases)
    elif component_type == 'converter':
        _registry.register_converter(name, component_class, aliases)
    elif component_type == 'validator':
        _registry.register_validator(name, component_class, aliases)
    else:
        raise ConfigurationError(f"Unknown component type: {component_type}")
