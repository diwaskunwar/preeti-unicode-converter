"""
Built-in Preeti font variants and their mappings.

This module provides pre-defined mappings for various Preeti font
variants including standard Preeti, Preeti Plus, and Kantipur fonts.
"""

from typing import Dict, List, Optional
import logging

from preeti_unicode.fonts.font_manager import FontMapping, FontRule, FontType, MappingType
from preeti_unicode.fonts.custom_fonts import FontDefinition, MappingRule


class PreetiVariantDetector:
    """
    Detector for identifying different Preeti font variants.
    
    Provides heuristics for distinguishing between different
    variants of Preeti fonts based on character patterns.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the Preeti variant detector.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        
        # Variant-specific character patterns
        self._variant_patterns = {
            'preeti_plus': [
                'ç', 'é', 'ñ', 'ó', 'ú', 'ü'  # Extended characters in Preeti Plus
            ],
            'kantipur': [
                'Ç', 'É', 'Ñ', 'Ó', 'Ú', 'Ü'  # Kantipur-specific characters
            ]
        }
    
    def detect_variant(self, text: str, font_name: Optional[str] = None) -> str:
        """
        Detect the Preeti font variant from text and font name.
        
        Args:
            text: Text content to analyze
            font_name: Optional font name
            
        Returns:
            Detected variant name ('standard', 'preeti_plus', 'kantipur')
        """
        # Check font name first
        if font_name:
            font_name_lower = font_name.lower()
            if 'plus' in font_name_lower:
                return 'preeti_plus'
            elif 'kantipur' in font_name_lower:
                return 'kantipur'
        
        # Analyze text content
        if text:
            # Check for Preeti Plus patterns
            plus_score = sum(1 for char in self._variant_patterns['preeti_plus'] if char in text)
            
            # Check for Kantipur patterns
            kantipur_score = sum(1 for char in self._variant_patterns['kantipur'] if char in text)
            
            if plus_score > kantipur_score and plus_score > 0:
                return 'preeti_plus'
            elif kantipur_score > 0:
                return 'kantipur'
        
        # Default to standard Preeti
        return 'standard'


class StandardPreetiMapping:
    """
    Standard Preeti font mapping to Unicode.
    
    Provides the most common Preeti to Unicode conversion
    rules used in standard Preeti fonts.
    """
    
    def __init__(self):
        """Initialize the standard Preeti mapping."""
        self.name = "standard_preeti"
        self.display_name = "Standard Preeti"
        self.description = "Standard Preeti font to Unicode conversion"
    
    def get_character_mappings(self) -> Dict[str, str]:
        """
        Get the character mappings for standard Preeti.
        
        Returns:
            Dictionary mapping Preeti characters to Unicode
        """
        return {
            # Lowercase letters (a-z)
            'a': 'ब', 'b': 'द', 'c': 'अ', 'd': 'म', 'e': 'भ',
            'f': 'ा', 'g': 'न', 'h': 'ज', 'i': 'ष्', 'j': 'व',
            'k': 'प', 'l': 'ि', 'm': 'फ', 'n': 'ल', 'o': 'य',
            'p': 'उ', 'q': 'त्र', 'r': 'च', 's': 'क', 't': 'त',
            'u': 'ग', 'v': 'ख', 'w': 'ध', 'x': 'ह', 'y': 'थ', 'z': 'श',
            
            # Uppercase letters (A-Z)
            'A': 'ब्', 'B': 'ध', 'C': 'ऋ', 'D': 'म्', 'E': 'भ्',
            'F': 'ँ', 'G': 'न्', 'H': 'ज्', 'I': 'क्ष्', 'J': 'व्',
            'K': 'प्', 'L': 'ी', 'M': 'ः', 'N': 'ल्', 'O': 'इ',
            'P': 'ए', 'Q': 'त्त', 'R': 'च्', 'S': 'क्', 'T': 'त्',
            'U': 'ग्', 'V': 'ख्', 'W': 'ध्', 'X': 'ह्', 'Y': 'थ्', 'Z': 'श्',
            
            # Numbers (0-9)
            '0': 'ण्', '1': 'ज्ञ', '2': 'द्द', '3': 'घ', '4': 'द्ध',
            '5': 'छ', '6': 'ट', '7': 'ठ', '8': 'ड', '9': 'ढ',
            
            # Special symbols
            '~': 'ञ्', '`': 'ञ', '!': '१', '@': '२', '#': '३', '$': '४',
            '%': '५', '^': '६', '&': '७', '*': '८', '(': '९', ')': '०',
            '-': '(', '_': ')', '+': 'ं', '[': 'ृ', '{': 'र्', ']': 'े',
            '}': 'ै', '\\': '्', '|': '्र', ';': 'स', ':': 'स्',
            "'": 'ु', '"': 'ू', ',': ',', '<': '?', '.': '।',
            '>': 'श्र', '/': 'र', '?': 'रु', '=': '.'
        }
    
    def get_special_rules(self) -> List[FontRule]:
        """
        Get special conversion rules that require context or patterns.
        
        Returns:
            List of special font rules
        """
        rules = []
        
        # Special combinations
        rules.append(FontRule(
            source='qm',
            target='स्',
            mapping_type=MappingType.CHARACTER,
            priority=10
        ))
        
        rules.append(FontRule(
            source='f]',
            target='ो',
            mapping_type=MappingType.CHARACTER,
            priority=10
        ))
        
        rules.append(FontRule(
            source='km',
            target='फ',
            mapping_type=MappingType.CHARACTER,
            priority=10
        ))
        
        rules.append(FontRule(
            source='0f',
            target='ण',
            mapping_type=MappingType.CHARACTER,
            priority=10
        ))
        
        rules.append(FontRule(
            source='If',
            target='क्ष',
            mapping_type=MappingType.CHARACTER,
            priority=10
        ))
        
        rules.append(FontRule(
            source='if',
            target='ष',
            mapping_type=MappingType.CHARACTER,
            priority=10
        ))
        
        rules.append(FontRule(
            source='cf',
            target='आ',
            mapping_type=MappingType.CHARACTER,
            priority=10
        ))
        
        return rules
    
    def create_mapping(self) -> FontMapping:
        """
        Create the complete font mapping.
        
        Returns:
            FontMapping instance for standard Preeti
        """
        # Create basic character rules
        rules = []
        char_mappings = self.get_character_mappings()
        
        for source, target in char_mappings.items():
            rule = FontRule(
                source=source,
                target=target,
                mapping_type=MappingType.CHARACTER,
                priority=1
            )
            rules.append(rule)
        
        # Add special rules
        rules.extend(self.get_special_rules())
        
        return FontMapping(
            name=self.name,
            source_font="preeti",
            target_font="unicode",
            font_type=FontType.PREETI,
            rules=rules,
            metadata={
                'display_name': self.display_name,
                'description': self.description,
                'author': 'Preeti Unicode Converter',
                'strategy': 'rule_based'
            }
        )


class PreetiPlusMapping(StandardPreetiMapping):
    """
    Preeti Plus font mapping to Unicode.
    
    Extends standard Preeti mapping with additional
    characters and rules specific to Preeti Plus fonts.
    """
    
    def __init__(self):
        """Initialize the Preeti Plus mapping."""
        super().__init__()
        self.name = "preeti_plus"
        self.display_name = "Preeti Plus"
        self.description = "Preeti Plus font to Unicode conversion with extended character set"
    
    def get_character_mappings(self) -> Dict[str, str]:
        """
        Get the character mappings for Preeti Plus.
        
        Returns:
            Dictionary mapping Preeti Plus characters to Unicode
        """
        # Start with standard mappings
        mappings = super().get_character_mappings()
        
        # Add Preeti Plus specific mappings
        plus_mappings = {
            'ç': 'ऽ',  # Avagraha
            'é': 'ॐ',  # Om symbol
            'ñ': 'ऑ',  # Candra O
            'ó': 'ऒ',  # Short O
            'ú': 'ॠ',  # Vocalic RR
            'ü': 'ॡ',  # Vocalic LL
        }
        
        mappings.update(plus_mappings)
        return mappings


class KantipurMapping(StandardPreetiMapping):
    """
    Kantipur font mapping to Unicode.
    
    Provides conversion rules specific to Kantipur fonts
    which have some variations from standard Preeti.
    """
    
    def __init__(self):
        """Initialize the Kantipur mapping."""
        super().__init__()
        self.name = "kantipur"
        self.display_name = "Kantipur"
        self.description = "Kantipur font to Unicode conversion"
    
    def get_character_mappings(self) -> Dict[str, str]:
        """
        Get the character mappings for Kantipur.
        
        Returns:
            Dictionary mapping Kantipur characters to Unicode
        """
        # Start with standard mappings
        mappings = super().get_character_mappings()
        
        # Override with Kantipur-specific mappings
        kantipur_overrides = {
            # Some characters may have different mappings in Kantipur
            'Ç': 'ऽ',  # Different from Preeti Plus
            'É': 'ॐ',
            'Ñ': 'ऑ',
            'Ó': 'ऒ',
            'Ú': 'ॠ',
            'Ü': 'ॡ',
        }
        
        mappings.update(kantipur_overrides)
        return mappings
    
    def get_special_rules(self) -> List[FontRule]:
        """
        Get special conversion rules for Kantipur.
        
        Returns:
            List of special font rules
        """
        # Start with standard rules
        rules = super().get_special_rules()
        
        # Add Kantipur-specific rules
        kantipur_rules = [
            FontRule(
                source='Qm',
                target='स्',
                mapping_type=MappingType.CHARACTER,
                priority=15
            ),
            # Add more Kantipur-specific rules as needed
        ]
        
        rules.extend(kantipur_rules)
        return rules


def create_builtin_font_definitions() -> List[FontDefinition]:
    """
    Create font definitions for all built-in Preeti variants.
    
    Returns:
        List of font definitions
    """
    definitions = []
    
    # Standard Preeti
    standard = StandardPreetiMapping()
    standard_def = FontDefinition(
        name=standard.name,
        display_name=standard.display_name,
        font_type="preeti",
        description=standard.description,
        author="Preeti Unicode Converter",
        source_font="preeti",
        target_font="unicode"
    )
    
    # Convert mappings to rules
    for source, target in standard.get_character_mappings().items():
        standard_def.add_rule(source, target)
    
    definitions.append(standard_def)
    
    # Preeti Plus
    plus = PreetiPlusMapping()
    plus_def = FontDefinition(
        name=plus.name,
        display_name=plus.display_name,
        font_type="preeti_plus",
        description=plus.description,
        author="Preeti Unicode Converter",
        source_font="preeti_plus",
        target_font="unicode"
    )
    
    for source, target in plus.get_character_mappings().items():
        plus_def.add_rule(source, target)
    
    definitions.append(plus_def)
    
    # Kantipur
    kantipur = KantipurMapping()
    kantipur_def = FontDefinition(
        name=kantipur.name,
        display_name=kantipur.display_name,
        font_type="kantipur",
        description=kantipur.description,
        author="Preeti Unicode Converter",
        source_font="kantipur",
        target_font="unicode"
    )
    
    for source, target in kantipur.get_character_mappings().items():
        kantipur_def.add_rule(source, target)
    
    definitions.append(kantipur_def)
    
    return definitions
