"""
Enhanced features for the Preeti Unicode converter.

This module provides advanced functionality including pipelines,
plugins, caching, and sophisticated processing capabilities.
"""

from preeti_unicode.enhanced.pipeline import (
    ProcessingPipeline,
    PipelineBuilder,
    PipelineStage,
    ConversionPipeline
)

from preeti_unicode.enhanced.plugins import (
    PluginManager,
    BaseConversionPlugin,
    FontMappingPlugin,
    NumberConversionPlugin,
    TextCleanupPlugin
)

from preeti_unicode.enhanced.cache import (
    CacheManager,
    MemoryCache,
    FileCache,
    create_cache
)

from preeti_unicode.enhanced.logging_system import (
    LoggingManager,
    StructuredLogger,
    setup_logging
)

from preeti_unicode.enhanced.pdf_processor import (
    PDFIntegrityValidator,
    EnhancedPDFReader
)

from preeti_unicode.enhanced.parallel_processor import (
    ParallelProcessor,
    BatchProcessor,
    TaskResult
)

__all__ = [
    # Pipeline
    'ProcessingPipeline', 'PipelineBuilder', 'PipelineStage', 'ConversionPipeline',
    
    # Plugins
    'PluginManager', 'BaseConversionPlugin', 'FontMappingPlugin',
    'NumberConversionPlugin', 'TextCleanupPlugin',
    
    # Cache
    'CacheManager', 'MemoryCache', 'FileCache', 'create_cache',
    
    # Logging
    'LoggingManager', 'StructuredLogger', 'setup_logging',
    
    # PDF Processing
    'PDFIntegrityValidator', 'EnhancedPDFReader',
    
    # Parallel Processing
    'ParallelProcessor', 'BatchProcessor', 'TaskResult'
]
