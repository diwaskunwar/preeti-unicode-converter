"""
File readers for different input formats.

This module contains reader classes for extracting text from various file formats
including PDF, DOCX, and TXT files.
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

try:
    import pymupdf as fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    from docx import Document
except ImportError:
    Document = None

from preeti_unicode.converter import is_preeti_font


class BaseReader(ABC):
    """Abstract base class for file readers."""
    
    @abstractmethod
    def read(self, file_path: Path, **kwargs) -> Dict[str, Any]:
        """
        Read content from a file.
        
        Args:
            file_path: Path to the file to read
            **kwargs: Additional options
            
        Returns:
            Dictionary containing extracted content
        """
        pass


class TXTReader(BaseReader):
    """Reader for plain text files."""
    
    def read(self, file_path: Path, encoding: str = 'utf-8', **kwargs) -> Dict[str, Any]:
        """
        Read content from a text file.
        
        Args:
            file_path: Path to the text file
            encoding: Text encoding (default: utf-8)
            **kwargs: Additional options
            
        Returns:
            Dictionary with 'text' key containing file content
        """
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                content = file.read()
            
            return {
                'text': content,
                'metadata': {
                    'file_path': str(file_path),
                    'file_size': file_path.stat().st_size,
                    'encoding': encoding
                }
            }
        except UnicodeDecodeError:
            # Try with different encodings
            for enc in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(file_path, 'r', encoding=enc) as file:
                        content = file.read()
                    return {
                        'text': content,
                        'metadata': {
                            'file_path': str(file_path),
                            'file_size': file_path.stat().st_size,
                            'encoding': enc
                        }
                    }
                except UnicodeDecodeError:
                    continue
            
            raise ValueError(f"Unable to decode text file: {file_path}")


class PDFReader(BaseReader):
    """Reader for PDF files."""
    
    def __init__(self):
        """Initialize PDF reader."""
        if fitz is None:
            raise ImportError("PyMuPDF is required for PDF reading. Install with: pip install PyMuPDF")
    
    def read(self, file_path: Path, **kwargs) -> Dict[str, Any]:
        """
        Read content from a PDF file.
        
        Args:
            file_path: Path to the PDF file
            **kwargs: Additional options
            
        Returns:
            Dictionary with 'pages' containing list of page content
        """
        try:
            doc = fitz.open(str(file_path))
            pages = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_content = self._extract_page_content(page, page_num)
                pages.append(page_content)
            
            doc.close()
            
            # Also provide combined text for simple use cases
            combined_text = '\n\n'.join([p['text'] for p in pages if p['text']])
            
            return {
                'text': combined_text,
                'pages': pages,
                'metadata': {
                    'file_path': str(file_path),
                    'file_size': file_path.stat().st_size,
                    'page_count': len(pages)
                }
            }
            
        except Exception as e:
            raise ValueError(f"Error reading PDF file {file_path}: {e}")
    
    def _extract_page_content(self, page, page_num: int) -> Dict[str, Any]:
        """
        Extract content from a single PDF page.
        
        Args:
            page: PyMuPDF page object
            page_num: Page number (0-based)
            
        Returns:
            Dictionary containing page content and metadata
        """
        blocks = page.get_text("dict")
        page_text = []
        font_info = []
        
        for block in blocks["blocks"]:
            if "lines" in block:
                block_text = ""
                for line in block["lines"]:
                    line_text = ""
                    for span in line["spans"]:
                        text = span["text"]
                        font = span.get("font", "")
                        
                        if text.strip():
                            line_text += text
                            font_info.append({
                                'text': text,
                                'font': font,
                                'is_preeti': is_preeti_font(font)
                            })
                    
                    if line_text.strip():
                        block_text += line_text + "\n"
                
                if block_text.strip():
                    page_text.append(block_text.strip())
        
        return {
            'text': "\n\n".join(page_text),
            'page_number': page_num + 1,
            'font_info': font_info,
            'blocks': page_text
        }


class DOCXReader(BaseReader):
    """Reader for DOCX files."""
    
    def __init__(self):
        """Initialize DOCX reader."""
        if Document is None:
            raise ImportError("python-docx is required for DOCX reading. Install with: pip install python-docx")
    
    def read(self, file_path: Path, **kwargs) -> Dict[str, Any]:
        """
        Read content from a DOCX file.
        
        Args:
            file_path: Path to the DOCX file
            **kwargs: Additional options
            
        Returns:
            Dictionary with text content and paragraph structure
        """
        try:
            doc = Document(str(file_path))
            paragraphs = []
            combined_text = []
            
            for para in doc.paragraphs:
                if para.text.strip():
                    paragraphs.append({
                        'text': para.text,
                        'style': para.style.name if para.style else None
                    })
                    combined_text.append(para.text)
            
            return {
                'text': '\n\n'.join(combined_text),
                'paragraphs': paragraphs,
                'metadata': {
                    'file_path': str(file_path),
                    'file_size': file_path.stat().st_size,
                    'paragraph_count': len(paragraphs)
                }
            }
            
        except Exception as e:
            raise ValueError(f"Error reading DOCX file {file_path}: {e}")


def create_reader(format_type: str) -> BaseReader:
    """
    Factory function to create appropriate reader for given format.
    
    Args:
        format_type: File format ('pdf', 'docx', 'txt')
        
    Returns:
        Appropriate reader instance
        
    Raises:
        ValueError: If format is not supported
    """
    format_type = format_type.lower()
    
    if format_type == 'pdf':
        return PDFReader()
    elif format_type == 'docx':
        return DOCXReader()
    elif format_type == 'txt':
        return TXTReader()
    else:
        raise ValueError(f"Unsupported format: {format_type}")


def read_file(file_path: Path, format_type: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """
    Read a file using the appropriate reader.
    
    Args:
        file_path: Path to the file
        format_type: File format (auto-detected if None)
        **kwargs: Additional options for the reader
        
    Returns:
        Dictionary containing file content
    """
    if format_type is None:
        # Auto-detect format from extension
        extension = file_path.suffix.lower()
        if extension == '.pdf':
            format_type = 'pdf'
        elif extension in ['.docx', '.doc']:
            format_type = 'docx'
        elif extension in ['.txt', '.text']:
            format_type = 'txt'
        else:
            raise ValueError(f"Cannot auto-detect format for file: {file_path}")
    
    reader = create_reader(format_type)
    return reader.read(file_path, **kwargs)
