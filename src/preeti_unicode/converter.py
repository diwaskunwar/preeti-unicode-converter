"""
Core conversion engine for Preeti to Unicode conversion.

This module contains the main conversion logic for transforming Preeti font text
to proper Unicode Nepali text, including Nepali numeral conversion.
"""

import re
from typing import Dict, List, Optional


class PreetiUnicodeConverter:
    """Core converter class for Preeti to Unicode conversion."""
    
    def __init__(self):
        """Initialize the converter with mapping dictionaries."""
        self._setup_mappings()
    
    def _setup_mappings(self) -> None:
        """Set up the character mapping dictionaries."""
        # Preeti lowercase to Unicode mapping (a-z)
        self.unicode_a_to_z = [
            "ब", "द", "अ", "म", "भ", "ा", "न", "ज", "ष्", "व",
            "प", "ि", "फ", "ल", "य", "उ", "त्र", "च", "क", "त",
            "ग", "ख", "ध", "ह", "थ", "श"
        ]
        
        # Preeti uppercase to Unicode mapping (A-Z)
        self.unicode_A_to_Z = [
            "ब्", "ध", "ऋ", "म्", "भ्", "ँ", "न्", "ज्", "क्ष्", "व्",
            "प्", "ी", "ः", "ल्", "इ", "ए", "त्त", "च्", "क्", "त्",
            "ग्", "ख्", "ध्", "ह्", "थ्", "श्"
        ]
        
        # Preeti numbers to Unicode mapping (0-9)
        self.unicode_0_to_9 = [
            "ण्", "ज्ञ", "द्द", "घ", "द्ध", "छ", "ट", "ठ", "ड", "ढ"
        ]
        
        # Special symbols mapping
        self.symbols_dict = {
            "~": "ञ्", "`": "ञ", "!": "१", "@": "२", "#": "३", "$": "४", 
            "%": "५", "^": "६", "&": "७", "*": "८", "(": "९", ")": "०",
            "-": "(", "_": ")", "+": "ं", "[": "ृ", "{": "र्", "]": "े", 
            "}": "ै", "\\": "्", "|": "्र", ";": "स", ":": "स्",
            "'": "ु", "\"": "ू", ",": ",", "<": "?", ".": "।", 
            ">": "श्र", "/": "र", "?": "रु", "=": ".", "ˆ": "फ्",
            "Î": "ङ्ख", "å": "द्व", "÷": "/", "«": "्र", "»": "्र", 
            "°": "्र", "¿": "्र", "¡": "्र"
        }
        
        # Nepali numerals mapping for number conversion
        self.nepali_numerals = {
            "0": "०", "1": "१", "2": "२", "3": "३", "4": "४",
            "5": "५", "6": "६", "7": "७", "8": "८", "9": "९"
        }
    
    def normalize_preeti(self, preeti_text: str) -> str:
        """
        Normalize Preeti text by handling special character combinations.
        
        Args:
            preeti_text: Raw Preeti text to normalize
            
        Returns:
            Normalized Preeti text ready for conversion
        """
        if not preeti_text:
            return ""
        
        normalized = ''
        previous_symbol = ''
        
        # Handle common Preeti character combinations
        text = preeti_text.replace('qm', 's|').replace('f]', 'ो').replace('km', 'फ')
        text = text.replace('0f', 'ण').replace('If', 'क्ष').replace('if', 'ष').replace('cf', 'आ')
        
        index = -1
        while index + 1 < len(text):
            index += 1
            character = text[index]
            
            try:
                # Handle special combinations with '{'
                if index + 2 < len(text) and text[index + 2] == '{':
                    if text[index + 1] == 'f' or text[index + 1] == 'ो':
                        normalized += '{' + character + text[index + 1]
                        index += 2
                        continue
                
                if index + 1 < len(text) and text[index + 1] == '{':
                    if character != 'f':
                        normalized += '{' + character
                        index += 1
                        continue
            except IndexError:
                pass
            
            # Handle 'l' character special case
            if character == 'l':
                previous_symbol = 'l'
                continue
            else:
                normalized += character + previous_symbol
                previous_symbol = ''
        
        return normalized
    
    def convert_to_unicode(self, preeti_text: str) -> str:
        """
        Convert Preeti text to Unicode.
        
        Args:
            preeti_text: Preeti text to convert
            
        Returns:
            Converted Unicode text
        """
        if not preeti_text:
            return ""
        
        converted = ''
        normalized_preeti = self.normalize_preeti(preeti_text)
        
        for character in normalized_preeti:
            try:
                char_code = ord(character)
                
                # Handle lowercase letters (a-z)
                if 97 <= char_code <= 122:  # a-z
                    converted += self.unicode_a_to_z[char_code - 97]
                # Handle uppercase letters (A-Z)
                elif 65 <= char_code <= 90:  # A-Z
                    converted += self.unicode_A_to_Z[char_code - 65]
                # Handle numbers (0-9)
                elif 48 <= char_code <= 57:  # 0-9
                    converted += self.unicode_0_to_9[char_code - 48]
                # Handle special symbols
                else:
                    converted += self.symbols_dict.get(character, character)
                    
            except (KeyError, IndexError):
                # If character not found in mappings, keep original
                converted += character
        
        return converted
    
    def convert_numbers_to_nepali(self, text: str) -> str:
        """
        Convert English numerals to Nepali numerals in the text.
        
        Args:
            text: Text containing English numerals
            
        Returns:
            Text with Nepali numerals
        """
        if not text:
            return ""
        
        result = ""
        for char in text:
            result += self.nepali_numerals.get(char, char)
        
        return result


# Global converter instance
_converter = PreetiUnicodeConverter()


def convert_text(text: str, convert_numbers: bool = True) -> str:
    """
    Convert Preeti text to Unicode.
    
    This is the main public API function for text conversion.
    
    Args:
        text: Preeti text to convert
        convert_numbers: Whether to convert English numerals to Nepali numerals
        
    Returns:
        Converted Unicode text
        
    Example:
        >>> from preeti_unicode import convert_text
        >>> result = convert_text("k]jL")
        >>> print(result)  # Output: केजल
    """
    if not text:
        return ""
    
    # Convert Preeti to Unicode
    unicode_text = _converter.convert_to_unicode(text)
    
    # Convert numbers if requested
    if convert_numbers:
        unicode_text = _converter.convert_numbers_to_nepali(unicode_text)
    
    return unicode_text


def is_preeti_font(font_name: Optional[str]) -> bool:
    """
    Check if a font name indicates Preeti font.
    
    Args:
        font_name: Name of the font to check
        
    Returns:
        True if the font appears to be Preeti font
    """
    if not font_name:
        return False
    
    font_name = font_name.lower()
    preeti_indicators = ['preeti', 'pcs', 'nepali']
    
    return any(indicator in font_name for indicator in preeti_indicators)
