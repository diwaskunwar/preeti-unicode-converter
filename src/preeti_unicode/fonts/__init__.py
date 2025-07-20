"""
Dynamic font support system for custom font mappings.

This module provides comprehensive support for custom font mappings,
user-defined conversion rules, and dynamic font loading.
"""

from preeti_unicode.fonts.font_manager import (
    FontManager,
    FontMapping,
    FontRule,
    FontDetector
)

from preeti_unicode.fonts.custom_fonts import (
    CustomFontLoader,
    FontDefinition,
    MappingRule,
    ConversionStrategy
)

from preeti_unicode.fonts.font_registry import (
    FontRegistry,
    register_font,
    get_font_mapping,
    list_available_fonts
)

from preeti_unicode.fonts.preeti_variants import (
    PreetiVariantDetector,
    StandardPreetiMapping,
    PreetiPlusMapping,
    KantipurMapping
)

__all__ = [
    # Font Manager
    'FontManager', 'FontMapping', 'FontRule', 'FontDetector',
    
    # Custom Fonts
    'CustomFontLoader', 'FontDefinition', 'MappingRule', 'ConversionStrategy',
    
    # Font Registry
    'FontRegistry', 'register_font', 'get_font_mapping', 'list_available_fonts',
    
    # Preeti Variants
    'PreetiVariantDetector', 'StandardPreetiMapping', 'PreetiPlusMapping', 'KantipurMapping'
]
