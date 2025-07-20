"""
Configuration management for the Preeti Unicode converter.

This module provides configuration classes and utilities for managing
application settings, logging, caching, and processing options.
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
import os
import json
import yaml
from enum import Enum

from preeti_unicode.core.exceptions import ConfigurationError


class LogLevel(Enum):
    """Logging level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class CacheType(Enum):
    """Cache type enumeration."""
    MEMORY = "memory"
    FILE = "file"
    REDIS = "redis"
    DISABLED = "disabled"


@dataclass
class LoggingConfig:
    """Configuration for logging settings."""
    level: LogLevel = LogLevel.INFO
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[Path] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    console_output: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'level': self.level.value,
            'format': self.format,
            'file_path': str(self.file_path) if self.file_path else None,
            'max_file_size': self.max_file_size,
            'backup_count': self.backup_count,
            'console_output': self.console_output
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LoggingConfig':
        """Create from dictionary format."""
        return cls(
            level=LogLevel(data.get('level', LogLevel.INFO.value)),
            format=data.get('format', "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            file_path=Path(data['file_path']) if data.get('file_path') else None,
            max_file_size=data.get('max_file_size', 10 * 1024 * 1024),
            backup_count=data.get('backup_count', 5),
            console_output=data.get('console_output', True)
        )


@dataclass
class CacheConfig:
    """Configuration for caching settings."""
    type: CacheType = CacheType.MEMORY
    max_size: int = 1000
    ttl_seconds: int = 3600  # 1 hour
    file_path: Optional[Path] = None
    redis_url: Optional[str] = None
    redis_db: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'type': self.type.value,
            'max_size': self.max_size,
            'ttl_seconds': self.ttl_seconds,
            'file_path': str(self.file_path) if self.file_path else None,
            'redis_url': self.redis_url,
            'redis_db': self.redis_db
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheConfig':
        """Create from dictionary format."""
        return cls(
            type=CacheType(data.get('type', CacheType.MEMORY.value)),
            max_size=data.get('max_size', 1000),
            ttl_seconds=data.get('ttl_seconds', 3600),
            file_path=Path(data['file_path']) if data.get('file_path') else None,
            redis_url=data.get('redis_url'),
            redis_db=data.get('redis_db', 0)
        )


@dataclass
class ProcessingConfig:
    """Configuration for processing settings."""
    max_workers: int = 4
    chunk_size: int = 1000
    timeout_seconds: float = 300.0  # 5 minutes
    retry_attempts: int = 3
    retry_delay: float = 1.0
    enable_progress_tracking: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'max_workers': self.max_workers,
            'chunk_size': self.chunk_size,
            'timeout_seconds': self.timeout_seconds,
            'retry_attempts': self.retry_attempts,
            'retry_delay': self.retry_delay,
            'enable_progress_tracking': self.enable_progress_tracking
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingConfig':
        """Create from dictionary format."""
        return cls(
            max_workers=data.get('max_workers', 4),
            chunk_size=data.get('chunk_size', 1000),
            timeout_seconds=data.get('timeout_seconds', 300.0),
            retry_attempts=data.get('retry_attempts', 3),
            retry_delay=data.get('retry_delay', 1.0),
            enable_progress_tracking=data.get('enable_progress_tracking', True)
        )


@dataclass
class FontConfig:
    """Configuration for font mappings and custom fonts."""
    custom_mappings: Dict[str, str] = field(default_factory=dict)
    font_files: Dict[str, Path] = field(default_factory=dict)
    default_font: str = "preeti"
    enable_auto_detection: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'custom_mappings': self.custom_mappings,
            'font_files': {k: str(v) for k, v in self.font_files.items()},
            'default_font': self.default_font,
            'enable_auto_detection': self.enable_auto_detection
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FontConfig':
        """Create from dictionary format."""
        font_files = {}
        if 'font_files' in data:
            font_files = {k: Path(v) for k, v in data['font_files'].items()}
        
        return cls(
            custom_mappings=data.get('custom_mappings', {}),
            font_files=font_files,
            default_font=data.get('default_font', 'preeti'),
            enable_auto_detection=data.get('enable_auto_detection', True)
        )


@dataclass
class Configuration:
    """Main configuration class containing all settings."""
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    fonts: FontConfig = field(default_factory=FontConfig)
    plugins: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    middleware: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'logging': self.logging.to_dict(),
            'cache': self.cache.to_dict(),
            'processing': self.processing.to_dict(),
            'fonts': self.fonts.to_dict(),
            'plugins': self.plugins,
            'middleware': self.middleware
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Configuration':
        """Create from dictionary format."""
        return cls(
            logging=LoggingConfig.from_dict(data.get('logging', {})),
            cache=CacheConfig.from_dict(data.get('cache', {})),
            processing=ProcessingConfig.from_dict(data.get('processing', {})),
            fonts=FontConfig.from_dict(data.get('fonts', {})),
            plugins=data.get('plugins', {}),
            middleware=data.get('middleware', [])
        )
    
    def save_to_file(self, file_path: Path) -> None:
        """
        Save configuration to file.
        
        Args:
            file_path: Path to save the configuration file
            
        Raises:
            ConfigurationError: If saving fails
        """
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = self.to_dict()
            
            if file_path.suffix.lower() == '.json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            elif file_path.suffix.lower() in ['.yml', '.yaml']:
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            else:
                raise ConfigurationError(
                    f"Unsupported configuration file format: {file_path.suffix}",
                    config_key="file_format"
                )
                
        except Exception as e:
            raise ConfigurationError(
                f"Failed to save configuration to {file_path}: {str(e)}",
                config_key="file_path",
                cause=e
            )
    
    @classmethod
    def load_from_file(cls, file_path: Path) -> 'Configuration':
        """
        Load configuration from file.
        
        Args:
            file_path: Path to the configuration file
            
        Returns:
            Configuration instance
            
        Raises:
            ConfigurationError: If loading fails
        """
        try:
            if not file_path.exists():
                raise ConfigurationError(
                    f"Configuration file not found: {file_path}",
                    config_key="file_path"
                )
            
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix.lower() == '.json':
                    data = json.load(f)
                elif file_path.suffix.lower() in ['.yml', '.yaml']:
                    data = yaml.safe_load(f)
                else:
                    raise ConfigurationError(
                        f"Unsupported configuration file format: {file_path.suffix}",
                        config_key="file_format"
                    )
            
            return cls.from_dict(data)
            
        except ConfigurationError:
            raise
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load configuration from {file_path}: {str(e)}",
                config_key="file_path",
                cause=e
            )
    
    @classmethod
    def load_from_env(cls, prefix: str = "PREETI_") -> 'Configuration':
        """
        Load configuration from environment variables.
        
        Args:
            prefix: Prefix for environment variables
            
        Returns:
            Configuration instance with values from environment
        """
        config = cls()
        
        # Logging configuration
        if f"{prefix}LOG_LEVEL" in os.environ:
            try:
                config.logging.level = LogLevel(os.environ[f"{prefix}LOG_LEVEL"])
            except ValueError:
                pass
        
        if f"{prefix}LOG_FILE" in os.environ:
            config.logging.file_path = Path(os.environ[f"{prefix}LOG_FILE"])
        
        # Cache configuration
        if f"{prefix}CACHE_TYPE" in os.environ:
            try:
                config.cache.type = CacheType(os.environ[f"{prefix}CACHE_TYPE"])
            except ValueError:
                pass
        
        if f"{prefix}CACHE_MAX_SIZE" in os.environ:
            try:
                config.cache.max_size = int(os.environ[f"{prefix}CACHE_MAX_SIZE"])
            except ValueError:
                pass
        
        # Processing configuration
        if f"{prefix}MAX_WORKERS" in os.environ:
            try:
                config.processing.max_workers = int(os.environ[f"{prefix}MAX_WORKERS"])
            except ValueError:
                pass
        
        if f"{prefix}TIMEOUT" in os.environ:
            try:
                config.processing.timeout_seconds = float(os.environ[f"{prefix}TIMEOUT"])
            except ValueError:
                pass
        
        return config


def get_default_config() -> Configuration:
    """
    Get default configuration.
    
    Returns:
        Default configuration instance
    """
    return Configuration()


def load_config(
    file_path: Optional[Path] = None,
    env_prefix: str = "PREETI_",
    use_defaults: bool = True
) -> Configuration:
    """
    Load configuration from multiple sources.
    
    Args:
        file_path: Optional path to configuration file
        env_prefix: Prefix for environment variables
        use_defaults: Whether to use default values as base
        
    Returns:
        Configuration instance
    """
    if use_defaults:
        config = get_default_config()
    else:
        config = Configuration()
    
    # Load from file if provided
    if file_path and file_path.exists():
        file_config = Configuration.load_from_file(file_path)
        # Merge configurations (file takes precedence)
        config = Configuration.from_dict({**config.to_dict(), **file_config.to_dict()})
    
    # Load from environment (takes highest precedence)
    env_config = Configuration.load_from_env(env_prefix)
    config = Configuration.from_dict({**config.to_dict(), **env_config.to_dict()})
    
    return config
