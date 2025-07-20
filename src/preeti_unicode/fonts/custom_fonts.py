"""
Custom font loading and definition system.

This module provides functionality for loading custom font definitions,
creating user-defined mappings, and implementing custom conversion strategies.
"""

import json
import yaml
from typing import Any, Dict, List, Optional, Union, Callable
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import logging

from preeti_unicode.fonts.font_manager import FontMapping, FontRule, FontType, MappingType
from preeti_unicode.core.exceptions import ConfigurationError, ValidationError


class ConversionStrategy(Enum):
    """Enumeration of conversion strategies."""
    SIMPLE = "simple"
    CONTEXTUAL = "contextual"
    PATTERN_BASED = "pattern_based"
    RULE_BASED = "rule_based"
    CUSTOM = "custom"


@dataclass
class MappingRule:
    """
    Simplified mapping rule for user-friendly font definitions.
    
    Provides a more accessible interface for defining conversion rules
    without requiring knowledge of the internal FontRule structure.
    """
    from_char: str
    to_char: str
    priority: int = 0
    before: Optional[str] = None
    after: Optional[str] = None
    description: Optional[str] = None
    
    def to_font_rule(self) -> FontRule:
        """
        Convert to internal FontRule format.
        
        Returns:
            FontRule instance
        """
        return FontRule(
            source=self.from_char,
            target=self.to_char,
            mapping_type=MappingType.CHARACTER,
            priority=self.priority,
            context_before=self.before,
            context_after=self.after,
            metadata={'description': self.description} if self.description else {}
        )


@dataclass
class FontDefinition:
    """
    Complete font definition for custom fonts.
    
    Provides a user-friendly way to define custom fonts with
    metadata, rules, and conversion strategies.
    """
    name: str
    display_name: str
    font_type: str = "custom"
    description: str = ""
    version: str = "1.0.0"
    author: str = ""
    source_font: str = ""
    target_font: str = "unicode"
    strategy: ConversionStrategy = ConversionStrategy.SIMPLE
    rules: List[MappingRule] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_rule(self, from_char: str, to_char: str, **kwargs) -> None:
        """
        Add a conversion rule.
        
        Args:
            from_char: Source character/pattern
            to_char: Target character/pattern
            **kwargs: Additional rule options
        """
        rule = MappingRule(from_char=from_char, to_char=to_char, **kwargs)
        self.rules.append(rule)
    
    def add_rules_from_dict(self, rules_dict: Dict[str, str]) -> None:
        """
        Add multiple rules from a dictionary.
        
        Args:
            rules_dict: Dictionary mapping source to target characters
        """
        for from_char, to_char in rules_dict.items():
            self.add_rule(from_char, to_char)
    
    def to_font_mapping(self) -> FontMapping:
        """
        Convert to internal FontMapping format.
        
        Returns:
            FontMapping instance
        """
        # Convert font type
        try:
            font_type = FontType(self.font_type.lower())
        except ValueError:
            font_type = FontType.CUSTOM
        
        # Convert rules
        font_rules = [rule.to_font_rule() for rule in self.rules]
        
        # Create mapping
        return FontMapping(
            name=self.name,
            source_font=self.source_font or self.name,
            target_font=self.target_font,
            font_type=font_type,
            rules=font_rules,
            metadata={
                'display_name': self.display_name,
                'description': self.description,
                'author': self.author,
                'strategy': self.strategy.value,
                **self.metadata
            },
            version=self.version
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary format.
        
        Returns:
            Dictionary representation
        """
        return {
            'name': self.name,
            'display_name': self.display_name,
            'font_type': self.font_type,
            'description': self.description,
            'version': self.version,
            'author': self.author,
            'source_font': self.source_font,
            'target_font': self.target_font,
            'strategy': self.strategy.value,
            'metadata': self.metadata,
            'rules': [
                {
                    'from_char': rule.from_char,
                    'to_char': rule.to_char,
                    'priority': rule.priority,
                    'before': rule.before,
                    'after': rule.after,
                    'description': rule.description
                }
                for rule in self.rules
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FontDefinition':
        """
        Create from dictionary format.
        
        Args:
            data: Dictionary representation
            
        Returns:
            FontDefinition instance
        """
        rules = []
        for rule_data in data.get('rules', []):
            rule = MappingRule(
                from_char=rule_data['from_char'],
                to_char=rule_data['to_char'],
                priority=rule_data.get('priority', 0),
                before=rule_data.get('before'),
                after=rule_data.get('after'),
                description=rule_data.get('description')
            )
            rules.append(rule)
        
        return cls(
            name=data['name'],
            display_name=data.get('display_name', data['name']),
            font_type=data.get('font_type', 'custom'),
            description=data.get('description', ''),
            version=data.get('version', '1.0.0'),
            author=data.get('author', ''),
            source_font=data.get('source_font', ''),
            target_font=data.get('target_font', 'unicode'),
            strategy=ConversionStrategy(data.get('strategy', 'simple')),
            rules=rules,
            metadata=data.get('metadata', {})
        )


class CustomFontLoader:
    """
    Loader for custom font definitions from various sources.
    
    Supports loading font definitions from JSON, YAML files,
    and programmatic creation with validation.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the custom font loader.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self._validators: List[Callable[[FontDefinition], List[str]]] = []
        
        # Add default validators
        self._add_default_validators()
    
    def _add_default_validators(self) -> None:
        """Add default validation functions."""
        
        def validate_basic_fields(definition: FontDefinition) -> List[str]:
            """Validate basic required fields."""
            errors = []
            
            if not definition.name:
                errors.append("Font name is required")
            
            if not definition.display_name:
                errors.append("Display name is required")
            
            if not definition.rules:
                errors.append("At least one conversion rule is required")
            
            return errors
        
        def validate_rules(definition: FontDefinition) -> List[str]:
            """Validate conversion rules."""
            errors = []
            
            for i, rule in enumerate(definition.rules):
                if not rule.from_char:
                    errors.append(f"Rule {i}: source character is required")
                
                if not rule.to_char:
                    errors.append(f"Rule {i}: target character is required")
            
            return errors
        
        self._validators.extend([validate_basic_fields, validate_rules])
    
    def add_validator(self, validator: Callable[[FontDefinition], List[str]]) -> None:
        """
        Add a custom validator function.
        
        Args:
            validator: Function that takes FontDefinition and returns list of error messages
        """
        self._validators.append(validator)
    
    def validate_definition(self, definition: FontDefinition) -> List[str]:
        """
        Validate a font definition.
        
        Args:
            definition: Font definition to validate
            
        Returns:
            List of validation error messages
        """
        all_errors = []
        
        for validator in self._validators:
            try:
                errors = validator(definition)
                all_errors.extend(errors)
            except Exception as e:
                all_errors.append(f"Validator error: {str(e)}")
        
        return all_errors
    
    def load_from_file(self, file_path: Path) -> FontDefinition:
        """
        Load font definition from a file.
        
        Args:
            file_path: Path to the font definition file
            
        Returns:
            Loaded font definition
            
        Raises:
            ConfigurationError: If file cannot be loaded or is invalid
        """
        if not file_path.exists():
            raise ConfigurationError(f"Font definition file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix.lower() == '.json':
                    data = json.load(f)
                elif file_path.suffix.lower() in ['.yml', '.yaml']:
                    data = yaml.safe_load(f)
                else:
                    raise ConfigurationError(f"Unsupported file format: {file_path.suffix}")
            
            definition = FontDefinition.from_dict(data)
            
            # Validate the definition
            errors = self.validate_definition(definition)
            if errors:
                raise ValidationError(
                    f"Font definition validation failed: {'; '.join(errors)}",
                    validation_errors=errors
                )
            
            self.logger.info(f"Loaded font definition: {definition.name} from {file_path}")
            return definition
            
        except (ValidationError, ConfigurationError):
            raise
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load font definition from {file_path}: {str(e)}",
                cause=e
            )
    
    def save_to_file(self, definition: FontDefinition, file_path: Path) -> None:
        """
        Save font definition to a file.
        
        Args:
            definition: Font definition to save
            file_path: Path where to save the definition
            
        Raises:
            ConfigurationError: If save fails
        """
        # Validate before saving
        errors = self.validate_definition(definition)
        if errors:
            raise ValidationError(
                f"Cannot save invalid font definition: {'; '.join(errors)}",
                validation_errors=errors
            )
        
        try:
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = definition.to_dict()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                if file_path.suffix.lower() == '.json':
                    json.dump(data, f, indent=2, ensure_ascii=False)
                elif file_path.suffix.lower() in ['.yml', '.yaml']:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
                else:
                    raise ConfigurationError(f"Unsupported file format: {file_path.suffix}")
            
            self.logger.info(f"Saved font definition: {definition.name} to {file_path}")
            
        except Exception as e:
            raise ConfigurationError(
                f"Failed to save font definition to {file_path}: {str(e)}",
                cause=e
            )
    
    def create_from_mapping_dict(
        self,
        name: str,
        mapping_dict: Dict[str, str],
        **kwargs
    ) -> FontDefinition:
        """
        Create a font definition from a simple mapping dictionary.
        
        Args:
            name: Name of the font
            mapping_dict: Dictionary mapping source to target characters
            **kwargs: Additional font definition options
            
        Returns:
            Created font definition
        """
        definition = FontDefinition(
            name=name,
            display_name=kwargs.get('display_name', name),
            **{k: v for k, v in kwargs.items() if k != 'display_name'}
        )
        
        definition.add_rules_from_dict(mapping_dict)
        
        # Validate the definition
        errors = self.validate_definition(definition)
        if errors:
            raise ValidationError(
                f"Created font definition is invalid: {'; '.join(errors)}",
                validation_errors=errors
            )
        
        return definition
    
    def load_from_directory(self, directory: Path) -> List[FontDefinition]:
        """
        Load all font definitions from a directory.
        
        Args:
            directory: Directory containing font definition files
            
        Returns:
            List of loaded font definitions
        """
        definitions = []
        
        if not directory.exists():
            self.logger.warning(f"Font definition directory not found: {directory}")
            return definitions
        
        for file_path in directory.glob("*.json"):
            try:
                definition = self.load_from_file(file_path)
                definitions.append(definition)
            except Exception as e:
                self.logger.error(f"Failed to load font definition from {file_path}: {e}")
        
        for file_path in directory.glob("*.yml"):
            try:
                definition = self.load_from_file(file_path)
                definitions.append(definition)
            except Exception as e:
                self.logger.error(f"Failed to load font definition from {file_path}: {e}")
        
        for file_path in directory.glob("*.yaml"):
            try:
                definition = self.load_from_file(file_path)
                definitions.append(definition)
            except Exception as e:
                self.logger.error(f"Failed to load font definition from {file_path}: {e}")
        
        self.logger.info(f"Loaded {len(definitions)} font definitions from {directory}")
        return definitions
