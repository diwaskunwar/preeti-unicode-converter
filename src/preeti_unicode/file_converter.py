"""
File conversion module for handling different input and output formats.

This module provides the file_converter function and supporting classes for
converting files between different formats while performing Preeti to Unicode conversion.
"""

import os
from pathlib import Path
from typing import Union, Optional, Dict, Any
from enum import Enum

from preeti_unicode.converter import convert_text, is_preeti_font
from preeti_unicode.readers import PDFReader, DOCXReader, TXTReader
from preeti_unicode.writers import PDFWriter, DOCXWriter, TXTWriter, HTMLWriter


class InputFormat(Enum):
    """Supported input file formats."""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"


class OutputFormat(Enum):
    """Supported output file formats."""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    HTML = "html"


class FileConverter:
    """Main file converter class."""
    
    def __init__(self):
        """Initialize the file converter with readers and writers."""
        self.readers = {
            InputFormat.PDF: PDFReader(),
            InputFormat.DOCX: DOCXReader(),
            InputFormat.TXT: TXTReader(),
        }
        
        self.writers = {
            OutputFormat.PDF: PDFWriter(),
            OutputFormat.DOCX: DOCXWriter(),
            OutputFormat.TXT: TXTWriter(),
            OutputFormat.HTML: HTMLWriter(),
        }
    
    def convert_file(
        self,
        input_file: Union[str, Path],
        input_format: Union[str, InputFormat],
        output_file: Union[str, Path],
        output_format: Union[str, OutputFormat],
        convert_numbers: bool = True,
        **kwargs
    ) -> bool:
        """
        Convert a file from one format to another with Preeti to Unicode conversion.
        
        Args:
            input_file: Path to the input file
            input_format: Format of the input file ('pdf', 'docx', 'txt')
            output_file: Path to the output file
            output_format: Format of the output file ('pdf', 'docx', 'txt', 'html')
            convert_numbers: Whether to convert English numerals to Nepali numerals
            **kwargs: Additional options for readers and writers
            
        Returns:
            True if conversion was successful, False otherwise
            
        Raises:
            FileNotFoundError: If input file doesn't exist
            ValueError: If unsupported format is specified
            PermissionError: If unable to write to output file
        """
        # Validate input file
        input_path = Path(input_file)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        # Normalize format enums
        if isinstance(input_format, str):
            try:
                input_format = InputFormat(input_format.lower())
            except ValueError:
                raise ValueError(f"Unsupported input format: {input_format}")
        
        if isinstance(output_format, str):
            try:
                output_format = OutputFormat(output_format.lower())
            except ValueError:
                raise ValueError(f"Unsupported output format: {output_format}")
        
        try:
            # Read the input file
            reader = self.readers[input_format]
            content = reader.read(input_path, **kwargs)
            
            # Convert the content
            converted_content = self._convert_content(content, convert_numbers)
            
            # Write the output file
            writer = self.writers[output_format]
            output_path = Path(output_file)
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            success = writer.write(converted_content, output_path, **kwargs)
            
            return success
            
        except Exception as e:
            print(f"Error during file conversion: {e}")
            return False
    
    def _convert_content(self, content: Dict[str, Any], convert_numbers: bool) -> Dict[str, Any]:
        """
        Convert the content from Preeti to Unicode.
        
        Args:
            content: Content dictionary from reader
            convert_numbers: Whether to convert numbers
            
        Returns:
            Converted content dictionary
        """
        converted_content = content.copy()
        
        # Convert text content
        if 'text' in content:
            converted_content['text'] = convert_text(content['text'], convert_numbers)
        
        # Convert pages if present (for multi-page documents)
        if 'pages' in content:
            converted_pages = []
            for page in content['pages']:
                if isinstance(page, dict) and 'text' in page:
                    converted_page = page.copy()
                    converted_page['text'] = convert_text(page['text'], convert_numbers)
                    converted_pages.append(converted_page)
                elif isinstance(page, str):
                    converted_pages.append(convert_text(page, convert_numbers))
                else:
                    converted_pages.append(page)
            converted_content['pages'] = converted_pages
        
        # Convert blocks if present (for structured documents)
        if 'blocks' in content:
            converted_blocks = []
            for block in content['blocks']:
                if isinstance(block, dict) and 'text' in block:
                    converted_block = block.copy()
                    converted_block['text'] = convert_text(block['text'], convert_numbers)
                    converted_blocks.append(converted_block)
                elif isinstance(block, str):
                    converted_blocks.append(convert_text(block, convert_numbers))
                else:
                    converted_blocks.append(block)
            converted_content['blocks'] = converted_blocks
        
        return converted_content
    
    def batch_convert(
        self,
        input_files: list,
        input_format: Union[str, InputFormat],
        output_dir: Union[str, Path],
        output_format: Union[str, OutputFormat],
        convert_numbers: bool = True,
        **kwargs
    ) -> Dict[str, bool]:
        """
        Convert multiple files in batch.
        
        Args:
            input_files: List of input file paths
            input_format: Format of input files
            output_dir: Directory for output files
            output_format: Format for output files
            convert_numbers: Whether to convert numbers
            **kwargs: Additional options
            
        Returns:
            Dictionary mapping input files to conversion success status
        """
        results = {}
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for input_file in input_files:
            input_path = Path(input_file)
            output_file = output_path / f"{input_path.stem}.{output_format.value}"
            
            try:
                success = self.convert_file(
                    input_file, input_format, output_file, output_format,
                    convert_numbers, **kwargs
                )
                results[str(input_file)] = success
            except Exception as e:
                print(f"Error converting {input_file}: {e}")
                results[str(input_file)] = False
        
        return results


# Global converter instance
_file_converter = FileConverter()


def file_converter(
    input_file: Union[str, Path],
    input_format: str,
    output_file: Union[str, Path],
    output_format: str,
    convert_numbers: bool = True,
    **kwargs
) -> bool:
    """
    Convert a file from one format to another with Preeti to Unicode conversion.
    
    This is the main public API function for file conversion.
    
    Args:
        input_file: Path to the input file
        input_format: Format of the input file ('pdf', 'docx', 'txt')
        output_file: Path to the output file
        output_format: Format of the output file ('pdf', 'docx', 'txt', 'html')
        convert_numbers: Whether to convert English numerals to Nepali numerals
        **kwargs: Additional options for readers and writers
        
    Returns:
        True if conversion was successful, False otherwise
        
    Example:
        >>> from preeti_unicode import file_converter
        >>> success = file_converter('input.pdf', 'pdf', 'output.txt', 'txt')
        >>> print(f"Conversion {'successful' if success else 'failed'}")
    """
    return _file_converter.convert_file(
        input_file, input_format, output_file, output_format,
        convert_numbers, **kwargs
    )
