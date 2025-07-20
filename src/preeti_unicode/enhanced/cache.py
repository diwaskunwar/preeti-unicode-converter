"""
Caching system for improved performance.

This module provides various caching implementations including
memory cache, file cache, and cache management utilities.
"""

import os
import pickle
import hashlib
import time
import threading
from typing import Any, Dict, Optional, Union, TypeVar, Generic
from pathlib import Path
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from collections import OrderedDict

from preeti_unicode.core.interfaces import ICache
from preeti_unicode.core.exceptions import CacheError
from preeti_unicode.core.config import CacheConfig, CacheType

K = TypeVar('K')
V = TypeVar('V')


@dataclass
class CacheEntry:
    """Represents a cache entry with metadata."""
    value: Any
    created_at: float
    ttl: Optional[float] = None
    access_count: int = 0
    last_accessed: float = 0
    
    def __post_init__(self):
        if self.last_accessed == 0:
            self.last_accessed = self.created_at
    
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl
    
    def touch(self) -> None:
        """Update access metadata."""
        self.access_count += 1
        self.last_accessed = time.time()


class MemoryCache(ICache[K, V]):
    """
    In-memory cache implementation with LRU eviction.
    
    Provides fast access to cached data with configurable
    size limits and TTL support.
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: Optional[float] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the memory cache.
        
        Args:
            max_size: Maximum number of entries to store
            default_ttl: Default time-to-live in seconds
            logger: Optional logger instance
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        
        self._cache: OrderedDict[K, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expired': 0
        }
    
    def get(self, key: K) -> Optional[V]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        with self._lock:
            if key not in self._cache:
                self._stats['misses'] += 1
                return None
            
            entry = self._cache[key]
            
            # Check if expired
            if entry.is_expired():
                del self._cache[key]
                self._stats['expired'] += 1
                self._stats['misses'] += 1
                return None
            
            # Update access metadata
            entry.touch()
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            
            self._stats['hits'] += 1
            return entry.value
    
    def set(self, key: K, value: V, ttl: Optional[float] = None) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)
        """
        with self._lock:
            # Use default TTL if not specified
            if ttl is None:
                ttl = self.default_ttl
            
            # Create cache entry
            entry = CacheEntry(
                value=value,
                created_at=time.time(),
                ttl=ttl
            )
            
            # Add to cache
            self._cache[key] = entry
            self._cache.move_to_end(key)
            
            # Evict if necessary
            self._evict_if_needed()
    
    def delete(self, key: K) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False if key not found
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cached values."""
        with self._lock:
            self._cache.clear()
            self._stats = {
                'hits': 0,
                'misses': 0,
                'evictions': 0,
                'expired': 0
            }
    
    def _evict_if_needed(self) -> None:
        """Evict least recently used entries if cache is full."""
        while len(self._cache) > self.max_size:
            # Remove least recently used item
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            self._stats['evictions'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary containing cache statistics
        """
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0
            
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hit_rate': hit_rate,
                **self._stats
            }
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.
        
        Returns:
            Number of expired entries removed
        """
        with self._lock:
            expired_keys = []
            
            for key, entry in self._cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
                self._stats['expired'] += 1
            
            return len(expired_keys)


class FileCache(ICache[str, Any]):
    """
    File-based cache implementation.
    
    Provides persistent caching using the filesystem
    with support for serialization and TTL.
    """
    
    def __init__(
        self,
        cache_dir: Path,
        default_ttl: Optional[float] = None,
        max_size: Optional[int] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the file cache.
        
        Args:
            cache_dir: Directory to store cache files
            default_ttl: Default time-to-live in seconds
            max_size: Maximum number of cache files (optional)
            logger: Optional logger instance
        """
        self.cache_dir = Path(cache_dir)
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        
        # Create cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from file cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        try:
            cache_file = self._get_cache_file(key)
            
            if not cache_file.exists():
                return None
            
            with self._lock:
                with open(cache_file, 'rb') as f:
                    entry = pickle.load(f)
                
                # Check if expired
                if entry.is_expired():
                    cache_file.unlink()
                    return None
                
                # Update access metadata
                entry.touch()
                
                # Save updated metadata
                with open(cache_file, 'wb') as f:
                    pickle.dump(entry, f)
                
                return entry.value
                
        except Exception as e:
            self.logger.error(f"Failed to get cache entry {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """
        Set value in file cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)
        """
        try:
            # Use default TTL if not specified
            if ttl is None:
                ttl = self.default_ttl
            
            # Create cache entry
            entry = CacheEntry(
                value=value,
                created_at=time.time(),
                ttl=ttl
            )
            
            cache_file = self._get_cache_file(key)
            
            with self._lock:
                with open(cache_file, 'wb') as f:
                    pickle.dump(entry, f)
            
            # Evict if necessary
            if self.max_size:
                self._evict_if_needed()
                
        except Exception as e:
            self.logger.error(f"Failed to set cache entry {key}: {e}")
            raise CacheError(
                f"Failed to set cache entry: {str(e)}",
                cache_key=key,
                operation="set",
                cause=e
            )
    
    def delete(self, key: str) -> bool:
        """
        Delete value from file cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False if key not found
        """
        try:
            cache_file = self._get_cache_file(key)
            
            if cache_file.exists():
                cache_file.unlink()
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to delete cache entry {key}: {e}")
            return False
    
    def clear(self) -> None:
        """Clear all cached files."""
        try:
            for cache_file in self.cache_dir.glob("*.cache"):
                cache_file.unlink()
        except Exception as e:
            self.logger.error(f"Failed to clear cache: {e}")
    
    def _get_cache_file(self, key: str) -> Path:
        """
        Get cache file path for a key.
        
        Args:
            key: Cache key
            
        Returns:
            Path to cache file
        """
        # Create a safe filename from the key
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"
    
    def _evict_if_needed(self) -> None:
        """Evict oldest cache files if limit is exceeded."""
        cache_files = list(self.cache_dir.glob("*.cache"))
        
        if len(cache_files) <= self.max_size:
            return
        
        # Sort by modification time (oldest first)
        cache_files.sort(key=lambda f: f.stat().st_mtime)
        
        # Remove oldest files
        files_to_remove = len(cache_files) - self.max_size
        for cache_file in cache_files[:files_to_remove]:
            try:
                cache_file.unlink()
            except Exception as e:
                self.logger.error(f"Failed to evict cache file {cache_file}: {e}")


class CacheManager:
    """
    Manager for multiple cache instances.
    
    Provides a unified interface for managing different
    types of caches and cache operations.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the cache manager.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self._caches: Dict[str, ICache] = {}
        self._default_cache: Optional[str] = None
    
    def add_cache(self, name: str, cache: ICache, is_default: bool = False) -> None:
        """
        Add a cache instance.
        
        Args:
            name: Name of the cache
            cache: Cache instance
            is_default: Whether this should be the default cache
        """
        self._caches[name] = cache
        
        if is_default or self._default_cache is None:
            self._default_cache = name
        
        self.logger.debug(f"Added cache: {name}")
    
    def get_cache(self, name: Optional[str] = None) -> Optional[ICache]:
        """
        Get a cache instance by name.
        
        Args:
            name: Name of the cache (uses default if None)
            
        Returns:
            Cache instance or None if not found
        """
        if name is None:
            name = self._default_cache
        
        return self._caches.get(name)
    
    def get(self, key: Any, cache_name: Optional[str] = None) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            cache_name: Name of the cache to use (uses default if None)
            
        Returns:
            Cached value or None if not found
        """
        cache = self.get_cache(cache_name)
        if cache is None:
            return None
        
        return cache.get(key)
    
    def set(self, key: Any, value: Any, ttl: Optional[float] = None, cache_name: Optional[str] = None) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            cache_name: Name of the cache to use (uses default if None)
        """
        cache = self.get_cache(cache_name)
        if cache is not None:
            cache.set(key, value, ttl)
    
    def delete(self, key: Any, cache_name: Optional[str] = None) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            cache_name: Name of the cache to use (uses default if None)
            
        Returns:
            True if deleted, False if key not found
        """
        cache = self.get_cache(cache_name)
        if cache is None:
            return False
        
        return cache.delete(key)
    
    def clear_all(self) -> None:
        """Clear all caches."""
        for cache in self._caches.values():
            cache.clear()


def create_cache(config: CacheConfig, logger: Optional[logging.Logger] = None) -> ICache:
    """
    Create a cache instance based on configuration.
    
    Args:
        config: Cache configuration
        logger: Optional logger instance
        
    Returns:
        Cache instance
        
    Raises:
        CacheError: If cache type is not supported
    """
    if config.type == CacheType.MEMORY:
        return MemoryCache(
            max_size=config.max_size,
            default_ttl=config.ttl_seconds,
            logger=logger
        )
    elif config.type == CacheType.FILE:
        if config.file_path is None:
            raise CacheError("File path is required for file cache")
        
        return FileCache(
            cache_dir=config.file_path,
            default_ttl=config.ttl_seconds,
            max_size=config.max_size,
            logger=logger
        )
    elif config.type == CacheType.DISABLED:
        return NoOpCache()
    else:
        raise CacheError(f"Unsupported cache type: {config.type}")


class NoOpCache(ICache):
    """No-operation cache that doesn't store anything."""
    
    def get(self, key: Any) -> Optional[Any]:
        return None
    
    def set(self, key: Any, value: Any, ttl: Optional[float] = None) -> None:
        pass
    
    def delete(self, key: Any) -> bool:
        return False
    
    def clear(self) -> None:
        pass


# Global cache manager instance
_cache_manager = CacheManager()


def get_cache_manager() -> CacheManager:
    """
    Get the global cache manager instance.
    
    Returns:
        Global cache manager
    """
    return _cache_manager
