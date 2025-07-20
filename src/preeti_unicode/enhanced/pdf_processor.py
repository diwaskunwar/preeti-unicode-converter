"""
Enhanced PDF processing with robust error handling and advanced features.

This module provides sophisticated PDF processing capabilities including
integrity validation, corruption handling, password protection support,
and progress tracking.
"""

import os
import hashlib
from typing import Any, Dict, List, Optional, Tuple, Callable
from pathlib import Path
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import pymupdf as fitz
except ImportError:
    fitz = None

from preeti_unicode.core.base_classes import BaseReader
from preeti_unicode.core.interfaces import IProgressTracker, ProcessingStatus
from preeti_unicode.core.exceptions import (
    FileProcessingError, ValidationError, DependencyError,
    ProcessingTimeoutError
)


class PDFIntegrityValidator:
    """
    Validator for PDF file integrity and structure.
    
    Provides comprehensive validation of PDF files including
    corruption detection, password protection checks, and structure validation.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the PDF integrity validator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(self.__class__.__name__)
    
    def validate_pdf(self, file_path: Path) -> Dict[str, Any]:
        """
        Perform comprehensive PDF validation.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary containing validation results and metadata
            
        Raises:
            FileProcessingError: If validation fails
            DependencyError: If PyMuPDF is not available
        """
        if fitz is None:
            raise DependencyError(
                "PyMuPDF is required for PDF processing",
                dependency_name="pymupdf"
            )
        
        try:
            validation_result = {
                'is_valid': False,
                'is_encrypted': False,
                'is_corrupted': False,
                'page_count': 0,
                'file_size': 0,
                'metadata': {},
                'errors': [],
                'warnings': []
            }
            
            # Basic file checks
            if not file_path.exists():
                validation_result['errors'].append("File does not exist")
                return validation_result
            
            if not file_path.is_file():
                validation_result['errors'].append("Path is not a file")
                return validation_result
            
            validation_result['file_size'] = file_path.stat().st_size
            
            # Check if file is empty
            if validation_result['file_size'] == 0:
                validation_result['errors'].append("File is empty")
                return validation_result
            
            # Try to open the PDF
            try:
                doc = fitz.open(str(file_path))
                
                # Check if encrypted
                validation_result['is_encrypted'] = doc.needs_pass
                
                if validation_result['is_encrypted']:
                    validation_result['warnings'].append("PDF is password protected")
                    doc.close()
                    return validation_result
                
                # Get basic metadata
                validation_result['page_count'] = len(doc)
                validation_result['metadata'] = doc.metadata
                
                # Validate each page
                corrupted_pages = []
                for page_num in range(len(doc)):
                    try:
                        page = doc.load_page(page_num)
                        # Try to extract text to verify page integrity
                        page.get_text()
                    except Exception as e:
                        corrupted_pages.append(page_num)
                        self.logger.warning(f"Page {page_num} appears corrupted: {e}")
                
                if corrupted_pages:
                    validation_result['is_corrupted'] = True
                    validation_result['errors'].append(f"Corrupted pages: {corrupted_pages}")
                else:
                    validation_result['is_valid'] = True
                
                doc.close()
                
            except Exception as e:
                validation_result['is_corrupted'] = True
                validation_result['errors'].append(f"Failed to open PDF: {str(e)}")
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"PDF validation failed for {file_path}: {e}")
            raise FileProcessingError(
                f"PDF validation failed: {str(e)}",
                file_path=file_path,
                operation="validate",
                cause=e
            )
    
    def check_password_protection(self, file_path: Path, password: Optional[str] = None) -> bool:
        """
        Check if PDF is password protected and optionally try to unlock it.
        
        Args:
            file_path: Path to the PDF file
            password: Optional password to try
            
        Returns:
            True if PDF can be accessed (not protected or correct password), False otherwise
        """
        try:
            doc = fitz.open(str(file_path))
            
            if not doc.needs_pass:
                doc.close()
                return True
            
            if password:
                success = doc.authenticate(password)
                doc.close()
                return success
            
            doc.close()
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to check password protection for {file_path}: {e}")
            return False


class EnhancedPDFReader(BaseReader):
    """
    Enhanced PDF reader with robust error handling and advanced features.
    
    Provides sophisticated PDF reading capabilities including progress tracking,
    parallel processing, and graceful error handling.
    """
    
    def __init__(
        self,
        validator: Optional[PDFIntegrityValidator] = None,
        progress_tracker: Optional[IProgressTracker] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the enhanced PDF reader.
        
        Args:
            validator: Optional PDF integrity validator
            progress_tracker: Optional progress tracker
            logger: Optional logger instance
        """
        super().__init__(logger)
        self.validator = validator or PDFIntegrityValidator(logger)
        self.progress_tracker = progress_tracker
        self._supported_extensions = ['.pdf']
    
    def _read_impl(self, file_path: Path, **kwargs) -> Dict[str, Any]:
        """
        Implement enhanced PDF reading with validation and progress tracking.
        
        Args:
            file_path: Path to the PDF file
            **kwargs: Additional reading options
            
        Returns:
            Dictionary containing extracted content and metadata
        """
        # Extract options
        password = kwargs.get('password')
        validate_integrity = kwargs.get('validate_integrity', True)
        extract_images = kwargs.get('extract_images', False)
        parallel_processing = kwargs.get('parallel_processing', True)
        max_workers = kwargs.get('max_workers', 4)
        timeout_seconds = kwargs.get('timeout_seconds', 300.0)
        
        # Validate PDF integrity
        if validate_integrity:
            self.logger.info(f"Validating PDF integrity: {file_path}")
            validation_result = self.validator.validate_pdf(file_path)
            
            if not validation_result['is_valid'] and not validation_result['is_encrypted']:
                raise ValidationError(
                    f"PDF validation failed: {', '.join(validation_result['errors'])}",
                    validation_errors=validation_result['errors']
                )
            
            if validation_result['is_encrypted'] and not password:
                raise ValidationError(
                    "PDF is password protected but no password provided",
                    field_name="password"
                )
        
        # Open PDF document
        try:
            doc = fitz.open(str(file_path))
            
            # Handle password protection
            if doc.needs_pass:
                if not password:
                    doc.close()
                    raise ValidationError(
                        "PDF is password protected but no password provided",
                        field_name="password"
                    )
                
                if not doc.authenticate(password):
                    doc.close()
                    raise ValidationError(
                        "Invalid password for PDF",
                        field_name="password"
                    )
            
            # Initialize progress tracking
            total_pages = len(doc)
            if self.progress_tracker:
                self.progress_tracker.start(total_pages, f"Reading PDF: {file_path.name}")
            
            # Process pages
            if parallel_processing and total_pages > 1:
                pages = self._process_pages_parallel(doc, max_workers, timeout_seconds)
            else:
                pages = self._process_pages_sequential(doc)
            
            # Extract document metadata
            metadata = {
                'title': doc.metadata.get('title', ''),
                'author': doc.metadata.get('author', ''),
                'subject': doc.metadata.get('subject', ''),
                'creator': doc.metadata.get('creator', ''),
                'producer': doc.metadata.get('producer', ''),
                'creation_date': doc.metadata.get('creationDate', ''),
                'modification_date': doc.metadata.get('modDate', ''),
                'page_count': total_pages,
                'is_encrypted': doc.needs_pass
            }
            
            doc.close()
            
            # Finalize progress tracking
            if self.progress_tracker:
                self.progress_tracker.finish("PDF reading completed")
            
            # Combine all page text
            combined_text = '\n\n'.join([p['text'] for p in pages if p['text']])
            
            return {
                'text': combined_text,
                'pages': pages,
                'metadata': metadata,
                'validation_result': validation_result if validate_integrity else None
            }
            
        except ValidationError:
            raise
        except Exception as e:
            if self.progress_tracker:
                self.progress_tracker.finish(f"Failed: {str(e)}")
            
            self.logger.error(f"Failed to read PDF {file_path}: {e}")
            raise FileProcessingError(
                f"Failed to read PDF: {str(e)}",
                file_path=file_path,
                operation="read",
                cause=e
            )
    
    def _process_pages_sequential(self, doc) -> List[Dict[str, Any]]:
        """
        Process PDF pages sequentially.
        
        Args:
            doc: PyMuPDF document object
            
        Returns:
            List of page content dictionaries
        """
        pages = []
        
        for page_num in range(len(doc)):
            try:
                page_content = self._extract_page_content(doc, page_num)
                pages.append(page_content)
                
                if self.progress_tracker:
                    self.progress_tracker.update(page_num + 1, f"Processed page {page_num + 1}")
                    
            except Exception as e:
                self.logger.warning(f"Failed to process page {page_num}: {e}")
                pages.append({
                    'text': '',
                    'page_number': page_num + 1,
                    'error': str(e),
                    'font_info': [],
                    'blocks': []
                })
        
        return pages
    
    def _process_pages_parallel(self, doc, max_workers: int, timeout_seconds: float) -> List[Dict[str, Any]]:
        """
        Process PDF pages in parallel.
        
        Args:
            doc: PyMuPDF document object
            max_workers: Maximum number of worker threads
            timeout_seconds: Timeout for parallel processing
            
        Returns:
            List of page content dictionaries
        """
        pages = [None] * len(doc)
        
        def process_page(page_num: int) -> Tuple[int, Dict[str, Any]]:
            try:
                page_content = self._extract_page_content(doc, page_num)
                return page_num, page_content
            except Exception as e:
                self.logger.warning(f"Failed to process page {page_num}: {e}")
                return page_num, {
                    'text': '',
                    'page_number': page_num + 1,
                    'error': str(e),
                    'font_info': [],
                    'blocks': []
                }
        
        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all page processing tasks
                future_to_page = {
                    executor.submit(process_page, page_num): page_num
                    for page_num in range(len(doc))
                }
                
                # Collect results with timeout
                completed_count = 0
                for future in as_completed(future_to_page, timeout=timeout_seconds):
                    page_num, page_content = future.result()
                    pages[page_num] = page_content
                    completed_count += 1
                    
                    if self.progress_tracker:
                        self.progress_tracker.update(completed_count, f"Processed page {page_num + 1}")
                
        except TimeoutError:
            raise ProcessingTimeoutError(
                f"PDF processing timed out after {timeout_seconds} seconds",
                timeout_seconds=timeout_seconds,
                operation="parallel_page_processing"
            )
        
        return pages
    
    def _extract_page_content(self, doc, page_num: int) -> Dict[str, Any]:
        """
        Extract content from a single PDF page.
        
        Args:
            doc: PyMuPDF document object
            page_num: Page number (0-based)
            
        Returns:
            Dictionary containing page content and metadata
        """
        from preeti_unicode.converter import is_preeti_font
        
        page = doc.load_page(page_num)
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
                                'is_preeti': is_preeti_font(font),
                                'size': span.get('size', 0),
                                'flags': span.get('flags', 0),
                                'bbox': span.get('bbox', [])
                            })
                    
                    if line_text.strip():
                        block_text += line_text + "\n"
                
                if block_text.strip():
                    page_text.append(block_text.strip())
        
        return {
            'text': "\n\n".join(page_text),
            'page_number': page_num + 1,
            'font_info': font_info,
            'blocks': page_text,
            'page_size': page.rect,
            'rotation': page.rotation
        }
