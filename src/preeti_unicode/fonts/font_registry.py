"""
Global font registry for managing all available font mappings.

This module provides a centralized registry for all font mappings,
including built-in fonts, custom fonts, and user-defined mappings.
"""

from typing import Dict, List, Optional, Set
from pathlib import Path
import logging

from preeti_unicode.fonts.font_manager import FontManager, FontMapping, get_font_manager
from preeti_unicode.fonts.custom_fonts import CustomFontLoader, FontDefinition
from preeti_unicode.core.exceptions import ConfigurationError


class FontRegistry:
    """
    Global registry for all font mappings.
    
    Provides a centralized system for registering, discovering,
    and managing all available font mappings.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the font registry.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.font_manager = get_font_manager()
        self.custom_loader = CustomFontLoader(logger)
        
        self._registered_fonts: Set[str] = set()
        self._font_directories: List[Path] = []
        
        # Initialize with built-in fonts
        self._register_builtin_fonts()
    
    def _register_builtin_fonts(self) -> None:
        """Register built-in font mappings."""
        try:
            # Import and register built-in Preeti variants
            from preeti_unicode.fonts.preeti_variants import (
                StandardPreetiMapping,
                PreetiPlusMapping,
                KantipurMapping
            )
            
            # Register standard Preeti mapping
            standard_mapping = StandardPreetiMapping().create_mapping()
            self.font_manager.register_mapping(standard_mapping, is_default=True)
            self._registered_fonts.add(standard_mapping.name)
            
            # Register Preeti Plus mapping
            plus_mapping = PreetiPlusMapping().create_mapping()
            self.font_manager.register_mapping(plus_mapping)
            self._registered_fonts.add(plus_mapping.name)
            
            # Register Kantipur mapping
            kantipur_mapping = KantipurMapping().create_mapping()
            self.font_manager.register_mapping(kantipur_mapping)
            self._registered_fonts.add(kantipur_mapping.name)
            
            self.logger.info("Registered built-in font mappings")
            
        except ImportError as e:
            self.logger.warning(f"Failed to import built-in font mappings: {e}")
        except Exception as e:
            self.logger.error(f"Failed to register built-in fonts: {e}")
    
    def register_font(self, font_definition: FontDefinition) -> None:
        """
        Register a custom font definition.
        
        Args:
            font_definition: Font definition to register
        """
        try:
            # Convert to font mapping
            mapping = font_definition.to_font_mapping()
            
            # Register with font manager
            self.font_manager.register_mapping(mapping)
            self._registered_fonts.add(mapping.name)
            
            self.logger.info(f"Registered custom font: {font_definition.name}")
            
        except Exception as e:
            self.logger.error(f"Failed to register font {font_definition.name}: {e}")
            raise ConfigurationError(
                f"Failed to register font: {str(e)}",
                config_key="font_registration",
                cause=e
            )
    
    def register_font_from_file(self, file_path: Path) -> None:
        """
        Register a font from a definition file.
        
        Args:
            file_path: Path to the font definition file
        """
        try:
            definition = self.custom_loader.load_from_file(file_path)
            self.register_font(definition)
            
        except Exception as e:
            self.logger.error(f"Failed to register font from {file_path}: {e}")
            raise
    
    def register_font_from_dict(self, name: str, mapping_dict: Dict[str, str], **kwargs) -> None:
        """
        Register a font from a simple mapping dictionary.
        
        Args:
            name: Name of the font
            mapping_dict: Dictionary mapping source to target characters
            **kwargs: Additional font definition options
        """
        try:
            definition = self.custom_loader.create_from_mapping_dict(name, mapping_dict, **kwargs)
            self.register_font(definition)
            
        except Exception as e:
            self.logger.error(f"Failed to register font from dictionary: {e}")
            raise
    
    def add_font_directory(self, directory: Path) -> None:
        """
        Add a directory to search for font definitions.
        
        Args:
            directory: Directory path to add
        """
        if directory not in self._font_directories:
            self._font_directories.append(directory)
            self.logger.debug(f"Added font directory: {directory}")
    
    def discover_fonts(self) -> int:
        """
        Discover and register fonts from all configured directories.
        
        Returns:
            Number of fonts discovered and registered
        """
        discovered_count = 0
        
        for directory in self._font_directories:
            try:
                definitions = self.custom_loader.load_from_directory(directory)
                
                for definition in definitions:
                    if definition.name not in self._registered_fonts:
                        self.register_font(definition)
                        discovered_count += 1
                    else:
                        self.logger.debug(f"Font {definition.name} already registered, skipping")
                        
            except Exception as e:
                self.logger.error(f"Failed to discover fonts in {directory}: {e}")
        
        if discovered_count > 0:
            self.logger.info(f"Discovered and registered {discovered_count} new fonts")
        
        return discovered_count
    
    def get_font_mapping(self, name: str) -> Optional[FontMapping]:
        """
        Get a font mapping by name.
        
        Args:
            name: Name of the font mapping
            
        Returns:
            Font mapping or None if not found
        """
        return self.font_manager.get_mapping(name)
    
    def list_available_fonts(self) -> List[str]:
        """
        List all available font names.
        
        Returns:
            List of font names
        """
        return list(self._registered_fonts)
    
    def get_font_info(self, name: str) -> Optional[Dict[str, any]]:
        """
        Get detailed information about a font.
        
        Args:
            name: Name of the font
            
        Returns:
            Dictionary containing font information or None if not found
        """
        mapping = self.get_font_mapping(name)
        if mapping is None:
            return None
        
        return {
            'name': mapping.name,
            'display_name': mapping.metadata.get('display_name', mapping.name),
            'description': mapping.metadata.get('description', ''),
            'author': mapping.metadata.get('author', ''),
            'version': mapping.version,
            'font_type': mapping.font_type.value,
            'source_font': mapping.source_font,
            'target_font': mapping.target_font,
            'rule_count': len(mapping.rules),
            'strategy': mapping.metadata.get('strategy', 'unknown')
        }
    
    def search_fonts(self, query: str) -> List[str]:
        """
        Search for fonts by name or description.
        
        Args:
            query: Search query
            
        Returns:
            List of matching font names
        """
        query_lower = query.lower()
        matches = []
        
        for font_name in self._registered_fonts:
            mapping = self.get_font_mapping(font_name)
            if mapping is None:
                continue
            
            # Check name
            if query_lower in font_name.lower():
                matches.append(font_name)
                continue
            
            # Check display name
            display_name = mapping.metadata.get('display_name', '')
            if query_lower in display_name.lower():
                matches.append(font_name)
                continue
            
            # Check description
            description = mapping.metadata.get('description', '')
            if query_lower in description.lower():
                matches.append(font_name)
                continue
        
        return matches
    
    def unregister_font(self, name: str) -> bool:
        """
        Unregister a font mapping.
        
        Args:
            name: Name of the font to unregister
            
        Returns:
            True if font was unregistered, False if not found
        """
        if name in self._registered_fonts:
            # Remove from font manager (if it supports removal)
            # For now, we just remove from our tracking
            self._registered_fonts.remove(name)
            self.logger.info(f"Unregistered font: {name}")
            return True
        
        return False
    
    def export_font_definition(self, name: str, file_path: Path) -> None:
        """
        Export a font mapping as a definition file.
        
        Args:
            name: Name of the font to export
            file_path: Path where to save the definition
            
        Raises:
            ConfigurationError: If font not found or export fails
        """
        mapping = self.get_font_mapping(name)
        if mapping is None:
            raise ConfigurationError(f"Font not found: {name}")
        
        try:
            # Convert mapping back to definition format
            definition_data = {
                'name': mapping.name,
                'display_name': mapping.metadata.get('display_name', mapping.name),
                'font_type': mapping.font_type.value,
                'description': mapping.metadata.get('description', ''),
                'version': mapping.version,
                'author': mapping.metadata.get('author', ''),
                'source_font': mapping.source_font,
                'target_font': mapping.target_font,
                'strategy': mapping.metadata.get('strategy', 'simple'),
                'metadata': {k: v for k, v in mapping.metadata.items() 
                           if k not in ['display_name', 'description', 'author', 'strategy']},
                'rules': [
                    {
                        'from_char': rule.source,
                        'to_char': rule.target,
                        'priority': rule.priority,
                        'before': rule.context_before,
                        'after': rule.context_after,
                        'description': rule.metadata.get('description')
                    }
                    for rule in mapping.rules
                ]
            }
            
            definition = FontDefinition.from_dict(definition_data)
            self.custom_loader.save_to_file(definition, file_path)
            
            self.logger.info(f"Exported font definition: {name} to {file_path}")
            
        except Exception as e:
            raise ConfigurationError(
                f"Failed to export font definition: {str(e)}",
                config_key="font_export",
                cause=e
            )


# Global font registry instance
_font_registry = FontRegistry()


def get_font_registry() -> FontRegistry:
    """
    Get the global font registry instance.
    
    Returns:
        Global font registry
    """
    return _font_registry


def register_font(font_definition: FontDefinition) -> None:
    """
    Register a font with the global registry.
    
    Args:
        font_definition: Font definition to register
    """
    _font_registry.register_font(font_definition)


def register_font_from_dict(name: str, mapping_dict: Dict[str, str], **kwargs) -> None:
    """
    Register a font from a mapping dictionary.
    
    Args:
        name: Name of the font
        mapping_dict: Dictionary mapping source to target characters
        **kwargs: Additional font definition options
    """
    _font_registry.register_font_from_dict(name, mapping_dict, **kwargs)


def get_font_mapping(name: str) -> Optional[FontMapping]:
    """
    Get a font mapping by name.
    
    Args:
        name: Name of the font mapping
        
    Returns:
        Font mapping or None if not found
    """
    return _font_registry.get_font_mapping(name)


def list_available_fonts() -> List[str]:
    """
    List all available font names.
    
    Returns:
        List of font names
    """
    return _font_registry.list_available_fonts()


def discover_fonts_in_directory(directory: Path) -> int:
    """
    Discover and register fonts from a directory.
    
    Args:
        directory: Directory to search for font definitions
        
    Returns:
        Number of fonts discovered and registered
    """
    _font_registry.add_font_directory(directory)
    return _font_registry.discover_fonts()
