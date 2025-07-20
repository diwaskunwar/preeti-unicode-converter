"""
Plugin system for extensible conversion functionality.

This module provides a flexible plugin architecture that allows
users to extend and customize the conversion process.
"""

import os
import importlib
import importlib.util
import inspect
from typing import Any, Dict, List, Optional, Type, Callable
from pathlib import Path
import logging
from abc import ABC, abstractmethod

from preeti_unicode.core.base_classes import BasePlugin
from preeti_unicode.core.exceptions import PluginError, ConfigurationError
from preeti_unicode.core.config import Configuration


class PluginManager:
    """
    Manager for loading, registering, and executing plugins.
    
    Provides a centralized system for managing plugins including
    discovery, loading, and lifecycle management.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the plugin manager.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self._plugins: Dict[str, BasePlugin] = {}
        self._plugin_configs: Dict[str, Dict[str, Any]] = {}
        self._plugin_directories: List[Path] = []
    
    def add_plugin_directory(self, directory: Path) -> None:
        """
        Add a directory to search for plugins.
        
        Args:
            directory: Directory path to add
        """
        if directory.exists() and directory.is_dir():
            self._plugin_directories.append(directory)
            self.logger.debug(f"Added plugin directory: {directory}")
        else:
            self.logger.warning(f"Plugin directory does not exist: {directory}")
    
    def register_plugin(self, plugin: BasePlugin, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Register a plugin instance.
        
        Args:
            plugin: Plugin instance to register
            config: Optional configuration for the plugin
        """
        plugin_name = plugin.get_name()
        
        if plugin_name in self._plugins:
            self.logger.warning(f"Plugin {plugin_name} is already registered, replacing")
        
        self._plugins[plugin_name] = plugin
        self._plugin_configs[plugin_name] = config or {}
        
        # Initialize the plugin
        try:
            plugin.initialize(self._plugin_configs[plugin_name])
            self.logger.info(f"Registered and initialized plugin: {plugin_name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize plugin {plugin_name}: {e}")
            # Remove the failed plugin
            del self._plugins[plugin_name]
            del self._plugin_configs[plugin_name]
            raise PluginError(
                f"Failed to initialize plugin {plugin_name}",
                plugin_name=plugin_name,
                cause=e
            )
    
    def load_plugins_from_directory(self, directory: Path) -> None:
        """
        Load plugins from a directory.
        
        Args:
            directory: Directory to load plugins from
        """
        if not directory.exists():
            self.logger.warning(f"Plugin directory does not exist: {directory}")
            return
        
        for file_path in directory.glob("*.py"):
            if file_path.name.startswith("__"):
                continue
            
            try:
                self._load_plugin_from_file(file_path)
            except Exception as e:
                self.logger.error(f"Failed to load plugin from {file_path}: {e}")
    
    def _load_plugin_from_file(self, file_path: Path) -> None:
        """
        Load a plugin from a Python file.
        
        Args:
            file_path: Path to the plugin file
        """
        module_name = file_path.stem
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        
        if spec is None or spec.loader is None:
            raise PluginError(f"Cannot load plugin module from {file_path}")
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find plugin classes in the module
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                issubclass(obj, BasePlugin) and 
                obj != BasePlugin):
                
                try:
                    # Create plugin instance
                    plugin = obj()
                    self.register_plugin(plugin)
                except Exception as e:
                    self.logger.error(f"Failed to instantiate plugin {name}: {e}")
    
    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """
        Get a plugin by name.
        
        Args:
            name: Name of the plugin
            
        Returns:
            Plugin instance or None if not found
        """
        return self._plugins.get(name)
    
    def list_plugins(self) -> List[str]:
        """
        List all registered plugin names.
        
        Returns:
            List of plugin names
        """
        return list(self._plugins.keys())
    
    def execute_plugin(self, name: str, data: Any, **kwargs) -> Any:
        """
        Execute a plugin by name.
        
        Args:
            name: Name of the plugin to execute
            data: Input data for the plugin
            **kwargs: Additional execution options
            
        Returns:
            Plugin output
            
        Raises:
            PluginError: If plugin is not found or execution fails
        """
        plugin = self.get_plugin(name)
        if plugin is None:
            raise PluginError(f"Plugin not found: {name}", plugin_name=name)
        
        return plugin.execute(data, **kwargs)
    
    def execute_plugins_by_type(self, plugin_type: Type, data: Any, **kwargs) -> List[Any]:
        """
        Execute all plugins of a specific type.
        
        Args:
            plugin_type: Type of plugins to execute
            data: Input data for the plugins
            **kwargs: Additional execution options
            
        Returns:
            List of plugin outputs
        """
        results = []
        
        for plugin in self._plugins.values():
            if isinstance(plugin, plugin_type):
                try:
                    result = plugin.execute(data, **kwargs)
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Plugin {plugin.get_name()} execution failed: {e}")
        
        return results


class BaseConversionPlugin(BasePlugin):
    """
    Base class for conversion plugins.
    
    Provides common functionality for plugins that modify
    the text conversion process.
    """
    
    def __init__(self, name: str, version: str = "1.0.0"):
        """
        Initialize the conversion plugin.
        
        Args:
            name: Plugin name
            version: Plugin version
        """
        super().__init__(name, version)
        self._priority = 0
    
    def get_priority(self) -> int:
        """
        Get the plugin priority.
        
        Returns:
            Plugin priority (higher values execute first)
        """
        return self._priority
    
    def set_priority(self, priority: int) -> None:
        """
        Set the plugin priority.
        
        Args:
            priority: Priority value
        """
        self._priority = priority


class FontMappingPlugin(BaseConversionPlugin):
    """
    Plugin for custom font character mappings.
    
    Allows users to define custom character mappings for
    specific fonts or conversion scenarios.
    """
    
    def __init__(self):
        """Initialize the font mapping plugin."""
        super().__init__("FontMapping", "1.0.0")
        self._custom_mappings: Dict[str, Dict[str, str]] = {}
    
    def _initialize_impl(self, config: Dict[str, Any]) -> None:
        """
        Initialize the plugin with custom mappings.
        
        Args:
            config: Plugin configuration containing mappings
        """
        self._custom_mappings = config.get('mappings', {})
        self.logger.info(f"Loaded {len(self._custom_mappings)} custom font mappings")
    
    def _execute_impl(self, data: Any, **kwargs) -> Any:
        """
        Apply custom font mappings to text.
        
        Args:
            data: Input text or data structure
            **kwargs: Additional options including font_name
            
        Returns:
            Text with custom mappings applied
        """
        if not isinstance(data, str):
            return data
        
        font_name = kwargs.get('font_name', 'default')
        
        if font_name not in self._custom_mappings:
            return data
        
        mappings = self._custom_mappings[font_name]
        result = data
        
        # Apply character mappings
        for source_char, target_char in mappings.items():
            result = result.replace(source_char, target_char)
        
        return result
    
    def add_mapping(self, font_name: str, source_char: str, target_char: str) -> None:
        """
        Add a custom character mapping.
        
        Args:
            font_name: Name of the font
            source_char: Source character
            target_char: Target character
        """
        if font_name not in self._custom_mappings:
            self._custom_mappings[font_name] = {}
        
        self._custom_mappings[font_name][source_char] = target_char


class NumberConversionPlugin(BaseConversionPlugin):
    """
    Plugin for custom number conversion rules.
    
    Provides flexible number conversion with support for
    different numeral systems and formatting rules.
    """
    
    def __init__(self):
        """Initialize the number conversion plugin."""
        super().__init__("NumberConversion", "1.0.0")
        self._conversion_rules: Dict[str, str] = {}
        self._enabled = True
    
    def _initialize_impl(self, config: Dict[str, Any]) -> None:
        """
        Initialize the plugin with conversion rules.
        
        Args:
            config: Plugin configuration
        """
        self._conversion_rules = config.get('rules', {
            "0": "०", "1": "१", "2": "२", "3": "३", "4": "४",
            "5": "५", "6": "६", "7": "७", "8": "८", "9": "९"
        })
        self._enabled = config.get('enabled', True)
    
    def _execute_impl(self, data: Any, **kwargs) -> Any:
        """
        Apply number conversion rules.
        
        Args:
            data: Input text
            **kwargs: Additional options
            
        Returns:
            Text with numbers converted
        """
        if not isinstance(data, str) or not self._enabled:
            return data
        
        result = data
        for source_num, target_num in self._conversion_rules.items():
            result = result.replace(source_num, target_num)
        
        return result


class TextCleanupPlugin(BaseConversionPlugin):
    """
    Plugin for text cleanup and normalization.
    
    Provides text cleaning functionality including whitespace
    normalization, character filtering, and formatting fixes.
    """
    
    def __init__(self):
        """Initialize the text cleanup plugin."""
        super().__init__("TextCleanup", "1.0.0")
        self._cleanup_rules: Dict[str, Any] = {}
    
    def _initialize_impl(self, config: Dict[str, Any]) -> None:
        """
        Initialize the plugin with cleanup rules.
        
        Args:
            config: Plugin configuration
        """
        self._cleanup_rules = config.get('rules', {
            'normalize_whitespace': True,
            'remove_extra_spaces': True,
            'trim_lines': True,
            'remove_empty_lines': False
        })
    
    def _execute_impl(self, data: Any, **kwargs) -> Any:
        """
        Apply text cleanup rules.
        
        Args:
            data: Input text
            **kwargs: Additional options
            
        Returns:
            Cleaned text
        """
        if not isinstance(data, str):
            return data
        
        result = data
        
        # Normalize whitespace
        if self._cleanup_rules.get('normalize_whitespace', False):
            import re
            result = re.sub(r'\s+', ' ', result)
        
        # Remove extra spaces
        if self._cleanup_rules.get('remove_extra_spaces', False):
            result = ' '.join(result.split())
        
        # Trim lines
        if self._cleanup_rules.get('trim_lines', False):
            lines = result.split('\n')
            result = '\n'.join(line.strip() for line in lines)
        
        # Remove empty lines
        if self._cleanup_rules.get('remove_empty_lines', False):
            lines = result.split('\n')
            result = '\n'.join(line for line in lines if line.strip())
        
        return result


# Global plugin manager instance
_plugin_manager = PluginManager()


def get_plugin_manager() -> PluginManager:
    """
    Get the global plugin manager instance.
    
    Returns:
        Global plugin manager
    """
    return _plugin_manager


def register_plugin(plugin: BasePlugin, config: Optional[Dict[str, Any]] = None) -> None:
    """
    Register a plugin with the global plugin manager.
    
    Args:
        plugin: Plugin instance to register
        config: Optional plugin configuration
    """
    _plugin_manager.register_plugin(plugin, config)


def load_plugins_from_config(config: Configuration) -> None:
    """
    Load plugins based on configuration.
    
    Args:
        config: Application configuration
    """
    plugin_configs = config.plugins
    
    for plugin_name, plugin_config in plugin_configs.items():
        plugin_type = plugin_config.get('type')
        
        if plugin_type == 'font_mapping':
            plugin = FontMappingPlugin()
            register_plugin(plugin, plugin_config)
        elif plugin_type == 'number_conversion':
            plugin = NumberConversionPlugin()
            register_plugin(plugin, plugin_config)
        elif plugin_type == 'text_cleanup':
            plugin = TextCleanupPlugin()
            register_plugin(plugin, plugin_config)
        else:
            _plugin_manager.logger.warning(f"Unknown plugin type: {plugin_type}")


def execute_conversion_plugins(text: str, **kwargs) -> str:
    """
    Execute all conversion plugins on text.
    
    Args:
        text: Input text
        **kwargs: Additional options
        
    Returns:
        Text processed by all plugins
    """
    plugins = []
    
    # Get all conversion plugins
    for plugin in _plugin_manager._plugins.values():
        if isinstance(plugin, BaseConversionPlugin):
            plugins.append(plugin)
    
    # Sort by priority (higher priority first)
    plugins.sort(key=lambda p: p.get_priority(), reverse=True)
    
    # Execute plugins in order
    result = text
    for plugin in plugins:
        try:
            result = plugin.execute(result, **kwargs)
        except Exception as e:
            _plugin_manager.logger.error(f"Plugin {plugin.get_name()} failed: {e}")
    
    return result
