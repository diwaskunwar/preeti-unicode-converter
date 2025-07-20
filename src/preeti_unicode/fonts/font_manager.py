"""
Font management system for dynamic font support.

This module provides comprehensive font management including
font detection, mapping management, and conversion rule handling.
"""

import re
import json
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import logging

from preeti_unicode.core.exceptions import ConfigurationError, ValidationError


class FontType(Enum):
    """Enumeration of supported font types."""
    PREETI = "preeti"
    PREETI_PLUS = "preeti_plus"
    KANTIPUR = "kantipur"
    CUSTOM = "custom"
    UNICODE = "unicode"


class MappingType(Enum):
    """Enumeration of mapping types."""
    CHARACTER = "character"
    PATTERN = "pattern"
    CONTEXTUAL = "contextual"
    COMPOSITE = "composite"


@dataclass
class FontRule:
    """
    Represents a single font conversion rule.
    
    A rule defines how to convert a specific character or pattern
    from one font to another with optional context conditions.
    """
    source: str
    target: str
    mapping_type: MappingType = MappingType.CHARACTER
    priority: int = 0
    context_before: Optional[str] = None
    context_after: Optional[str] = None
    conditions: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def matches_context(self, text: str, position: int) -> bool:
        """
        Check if the rule matches the context at the given position.
        
        Args:
            text: Full text being processed
            position: Position of the character/pattern
            
        Returns:
            True if context matches, False otherwise
        """
        # Check before context
        if self.context_before:
            start_pos = max(0, position - len(self.context_before))
            before_text = text[start_pos:position]
            if not before_text.endswith(self.context_before):
                return False
        
        # Check after context
        if self.context_after:
            end_pos = min(len(text), position + len(self.source) + len(self.context_after))
            after_text = text[position + len(self.source):end_pos]
            if not after_text.startswith(self.context_after):
                return False
        
        return True
    
    def apply(self, text: str, position: int) -> Tuple[str, int]:
        """
        Apply the rule to text at the given position.
        
        Args:
            text: Text to modify
            position: Position to apply the rule
            
        Returns:
            Tuple of (modified_text, new_position)
        """
        if self.mapping_type == MappingType.CHARACTER:
            # Simple character replacement
            new_text = text[:position] + self.target + text[position + len(self.source):]
            new_position = position + len(self.target)
            return new_text, new_position
        
        elif self.mapping_type == MappingType.PATTERN:
            # Pattern-based replacement using regex
            pattern = re.compile(self.source)
            match = pattern.match(text, position)
            if match:
                new_text = text[:position] + self.target + text[match.end():]
                new_position = position + len(self.target)
                return new_text, new_position
        
        # If no match or unsupported type, return unchanged
        return text, position + 1


@dataclass
class FontMapping:
    """
    Complete font mapping definition.
    
    Contains all rules and metadata for converting text
    from one font to another.
    """
    name: str
    source_font: str
    target_font: str
    font_type: FontType
    rules: List[FontRule] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"
    
    def __post_init__(self):
        """Sort rules by priority after initialization."""
        self.rules.sort(key=lambda r: r.priority, reverse=True)
    
    def add_rule(self, rule: FontRule) -> None:
        """
        Add a conversion rule to the mapping.
        
        Args:
            rule: Rule to add
        """
        self.rules.append(rule)
        # Re-sort rules by priority
        self.rules.sort(key=lambda r: r.priority, reverse=True)
    
    def remove_rule(self, source: str, target: str) -> bool:
        """
        Remove a conversion rule from the mapping.
        
        Args:
            source: Source pattern of the rule to remove
            target: Target pattern of the rule to remove
            
        Returns:
            True if rule was found and removed, False otherwise
        """
        for i, rule in enumerate(self.rules):
            if rule.source == source and rule.target == target:
                del self.rules[i]
                return True
        return False
    
    def convert_text(self, text: str) -> str:
        """
        Convert text using this font mapping.
        
        Args:
            text: Text to convert
            
        Returns:
            Converted text
        """
        if not text:
            return text
        
        result = text
        position = 0
        
        while position < len(result):
            rule_applied = False
            
            # Try each rule in priority order
            for rule in self.rules:
                # Check if rule matches at current position
                if (position + len(rule.source) <= len(result) and
                    result[position:position + len(rule.source)] == rule.source):
                    
                    # Check context if specified
                    if rule.matches_context(result, position):
                        # Apply the rule
                        result, new_position = rule.apply(result, position)
                        position = new_position
                        rule_applied = True
                        break
            
            # If no rule was applied, move to next character
            if not rule_applied:
                position += 1
        
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert mapping to dictionary format.
        
        Returns:
            Dictionary representation
        """
        return {
            'name': self.name,
            'source_font': self.source_font,
            'target_font': self.target_font,
            'font_type': self.font_type.value,
            'version': self.version,
            'metadata': self.metadata,
            'rules': [
                {
                    'source': rule.source,
                    'target': rule.target,
                    'mapping_type': rule.mapping_type.value,
                    'priority': rule.priority,
                    'context_before': rule.context_before,
                    'context_after': rule.context_after,
                    'conditions': rule.conditions,
                    'metadata': rule.metadata
                }
                for rule in self.rules
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FontMapping':
        """
        Create mapping from dictionary format.
        
        Args:
            data: Dictionary representation
            
        Returns:
            FontMapping instance
        """
        rules = []
        for rule_data in data.get('rules', []):
            rule = FontRule(
                source=rule_data['source'],
                target=rule_data['target'],
                mapping_type=MappingType(rule_data.get('mapping_type', 'character')),
                priority=rule_data.get('priority', 0),
                context_before=rule_data.get('context_before'),
                context_after=rule_data.get('context_after'),
                conditions=rule_data.get('conditions', {}),
                metadata=rule_data.get('metadata', {})
            )
            rules.append(rule)
        
        return cls(
            name=data['name'],
            source_font=data['source_font'],
            target_font=data['target_font'],
            font_type=FontType(data.get('font_type', 'custom')),
            rules=rules,
            metadata=data.get('metadata', {}),
            version=data.get('version', '1.0.0')
        )


class FontDetector:
    """
    Font detection system for identifying font types from text or metadata.
    
    Provides automatic font detection based on character patterns,
    font names, and other heuristics.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the font detector.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        
        # Font detection patterns
        self._font_patterns = {
            FontType.PREETI: [
                r'preeti',
                r'pcs',
                r'nepali'
            ],
            FontType.PREETI_PLUS: [
                r'preeti\s*plus',
                r'preeti\+',
                r'pcs\s*plus'
            ],
            FontType.KANTIPUR: [
                r'kantipur',
                r'kantipurnews'
            ]
        }
        
        # Character-based detection patterns
        self._character_patterns = {
            FontType.PREETI: [
                r'[a-zA-Z0-9]+',  # Contains ASCII characters
                r'[~`!@#$%^&*()_+\[\]{}\\|;:\'",.<>/?]+'  # Special symbols
            ],
            FontType.UNICODE: [
                r'[\u0900-\u097F]+',  # Devanagari Unicode range
                r'[०-९]+'  # Nepali numerals
            ]
        }
    
    def detect_font_from_name(self, font_name: str) -> Optional[FontType]:
        """
        Detect font type from font name.
        
        Args:
            font_name: Name of the font
            
        Returns:
            Detected font type or None if not recognized
        """
        if not font_name:
            return None
        
        font_name_lower = font_name.lower()
        
        for font_type, patterns in self._font_patterns.items():
            for pattern in patterns:
                if re.search(pattern, font_name_lower):
                    self.logger.debug(f"Detected font type {font_type.value} from name: {font_name}")
                    return font_type
        
        return None
    
    def detect_font_from_text(self, text: str) -> Optional[FontType]:
        """
        Detect font type from text content.
        
        Args:
            text: Text content to analyze
            
        Returns:
            Detected font type or None if not recognized
        """
        if not text:
            return None
        
        # Count matches for each font type
        type_scores = {}
        
        for font_type, patterns in self._character_patterns.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, text)
                score += sum(len(match) for match in matches)
            
            if score > 0:
                type_scores[font_type] = score
        
        if not type_scores:
            return None
        
        # Return the font type with highest score
        detected_type = max(type_scores, key=type_scores.get)
        self.logger.debug(f"Detected font type {detected_type.value} from text analysis")
        
        return detected_type
    
    def is_preeti_font(self, font_name: Optional[str]) -> bool:
        """
        Check if a font name indicates Preeti font.
        
        Args:
            font_name: Name of the font to check
            
        Returns:
            True if the font appears to be Preeti font
        """
        detected_type = self.detect_font_from_name(font_name or "")
        return detected_type in [FontType.PREETI, FontType.PREETI_PLUS, FontType.KANTIPUR]


class FontManager:
    """
    Central manager for font mappings and conversions.
    
    Provides a unified interface for managing multiple font mappings,
    detecting fonts, and performing conversions.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the font manager.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.detector = FontDetector(logger)
        
        self._mappings: Dict[str, FontMapping] = {}
        self._default_mapping: Optional[str] = None
    
    def register_mapping(self, mapping: FontMapping, is_default: bool = False) -> None:
        """
        Register a font mapping.
        
        Args:
            mapping: Font mapping to register
            is_default: Whether this should be the default mapping
        """
        self._mappings[mapping.name] = mapping
        
        if is_default or self._default_mapping is None:
            self._default_mapping = mapping.name
        
        self.logger.info(f"Registered font mapping: {mapping.name}")
    
    def get_mapping(self, name: Optional[str] = None) -> Optional[FontMapping]:
        """
        Get a font mapping by name.
        
        Args:
            name: Name of the mapping (uses default if None)
            
        Returns:
            Font mapping or None if not found
        """
        if name is None:
            name = self._default_mapping
        
        return self._mappings.get(name)
    
    def list_mappings(self) -> List[str]:
        """
        List all registered mapping names.
        
        Returns:
            List of mapping names
        """
        return list(self._mappings.keys())
    
    def convert_text(
        self,
        text: str,
        mapping_name: Optional[str] = None,
        auto_detect: bool = True
    ) -> str:
        """
        Convert text using a font mapping.
        
        Args:
            text: Text to convert
            mapping_name: Name of the mapping to use (auto-detect if None)
            auto_detect: Whether to auto-detect font type
            
        Returns:
            Converted text
        """
        if not text:
            return text
        
        # Auto-detect mapping if not specified
        if mapping_name is None and auto_detect:
            detected_type = self.detector.detect_font_from_text(text)
            if detected_type:
                # Find a mapping for the detected type
                for mapping in self._mappings.values():
                    if mapping.font_type == detected_type:
                        mapping_name = mapping.name
                        break
        
        # Use default mapping if still not found
        if mapping_name is None:
            mapping_name = self._default_mapping
        
        # Get the mapping
        mapping = self.get_mapping(mapping_name)
        if mapping is None:
            self.logger.warning(f"No mapping found: {mapping_name}")
            return text
        
        # Convert the text
        self.logger.debug(f"Converting text using mapping: {mapping_name}")
        return mapping.convert_text(text)
    
    def load_mapping_from_file(self, file_path: Path) -> FontMapping:
        """
        Load a font mapping from a JSON file.
        
        Args:
            file_path: Path to the mapping file
            
        Returns:
            Loaded font mapping
            
        Raises:
            ConfigurationError: If file cannot be loaded
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            mapping = FontMapping.from_dict(data)
            self.register_mapping(mapping)
            
            self.logger.info(f"Loaded font mapping from: {file_path}")
            return mapping
            
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load font mapping from {file_path}: {str(e)}",
                config_key="font_mapping_file",
                cause=e
            )
    
    def save_mapping_to_file(self, mapping_name: str, file_path: Path) -> None:
        """
        Save a font mapping to a JSON file.
        
        Args:
            mapping_name: Name of the mapping to save
            file_path: Path where to save the mapping
            
        Raises:
            ConfigurationError: If mapping not found or save fails
        """
        mapping = self.get_mapping(mapping_name)
        if mapping is None:
            raise ConfigurationError(f"Mapping not found: {mapping_name}")
        
        try:
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(mapping.to_dict(), f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved font mapping to: {file_path}")
            
        except Exception as e:
            raise ConfigurationError(
                f"Failed to save font mapping to {file_path}: {str(e)}",
                config_key="font_mapping_file",
                cause=e
            )


# Global font manager instance
_font_manager = FontManager()


def get_font_manager() -> FontManager:
    """
    Get the global font manager instance.

    Returns:
        Global font manager
    """
    return _font_manager
