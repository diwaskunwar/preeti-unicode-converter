"""
Preeti Unicode Converter

A highly customizable Python package for converting Preeti font text to Unicode (Nepali).
Supports multiple input and output formats including PDF, DOCX, and TXT files.
"""

__version__ = "0.1.0"
__author__ = "Diwas Kunwar"
__email__ = "diwas.kuwar@gmail.com"

from preeti_unicode.converter import convert_text
from preeti_unicode.file_converter import file_converter
from preeti_unicode.test_utils import test

__all__ = ["convert_text", "file_converter", "test"]
