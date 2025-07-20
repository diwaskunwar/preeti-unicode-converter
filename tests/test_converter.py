"""Basic tests for the preeti unicode converter."""

import pytest
from preeti_unicode.converter import PreetiUnicodeConverter


class TestPreetiUnicodeConverter:
    """Test cases for PreetiUnicodeConverter."""
    
    def test_converter_initialization(self):
        """Test that converter can be initialized."""
        converter = PreetiUnicodeConverter()
        assert converter is not None
    
    def test_basic_conversion(self):
        """Test basic text conversion functionality."""
        converter = PreetiUnicodeConverter()
        
        # Add some basic test cases here
        # Example: test_text = "some preeti text"
        # expected = "expected unicode output"
        # result = converter.convert(test_text)
        # assert result == expected
        
        # For now, just test that the method exists
        assert hasattr(converter, 'convert')
    
    def test_empty_string_conversion(self):
        """Test conversion of empty string."""
        converter = PreetiUnicodeConverter()
        result = converter.convert("")
        assert result == ""
    
    def test_none_input_handling(self):
        """Test handling of None input."""
        converter = PreetiUnicodeConverter()
        with pytest.raises((TypeError, ValueError)):
            converter.convert(None)
