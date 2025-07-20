# Preeti Unicode Converter

A highly customizable Python package for converting Preeti font text to Unicode (Nepali). Supports multiple input and output formats including PDF, DOCX, and TXT files with enterprise-level features.

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PyPI Version](https://img.shields.io/badge/pypi-v0.1.0-orange.svg)](https://pypi.org/project/preeti-unicode/)

## Features

### Core Functionality
- **Text Conversion**: Convert Preeti font text to proper Unicode Nepali text
- **Multiple Formats**: Support for PDF, DOCX, TXT, and HTML files
- **Batch Processing**: Convert multiple files simultaneously with parallel processing
- **CLI Interface**: Command-line tool for easy integration into workflows

### Advanced Features
- **Dynamic Font Support**: Add custom font mappings and user-defined conversion rules
- **Plugin Architecture**: Extensible system for custom conversion logic
- **Processing Pipelines**: Configurable conversion workflows with middleware support
- **Caching System**: Improved performance with intelligent caching
- **Progress Tracking**: Real-time progress monitoring for large operations
- **Error Handling**: Comprehensive error management with graceful degradation

### Enterprise Features
- **PDF Processing**: Robust PDF handling with integrity validation and corruption detection
- **Parallel Processing**: Multi-threaded processing for high-performance batch operations
- **Logging System**: Structured logging with multiple output formats
- **Configuration Management**: Flexible configuration system with environment variable support

## Installation

### Using pip (Recommended)
```bash
pip install preeti-unicode
```

### Using uv (Fast)
```bash
uv add preeti-unicode
```

### From Source
```bash
git clone https://github.com/diwaskunwar/preeti-unicode.git
cd preeti-unicode
pip install -e .
```

## Quick Start

### Basic Text Conversion
```python
from preeti_unicode import convert_text

# Convert Preeti text to Unicode
result = convert_text("g]kfn")
print(result)  # Output: नेपाल

# Convert with custom options
result = convert_text("g]kfn @)!&", convert_numbers=True)
print(result)  # Output: नेपाल २०१७
```

### File Conversion
```python
from preeti_unicode import file_converter

# Convert a PDF file to Unicode text
success = file_converter(
    input_file="document.pdf",
    input_format="pdf",
    output_file="converted.txt",
    output_format="txt"
)

# Convert DOCX to HTML
success = file_converter(
    input_file="document.docx",
    input_format="docx",
    output_file="converted.html",
    output_format="html"
)
```

### Quick Testing
```python
from preeti_unicode import test

# Test string conversion
test("string", "g]kfn")

# Test file conversion capabilities
test("txt")    # Test TXT file conversion
test("pdf")    # Test PDF file conversion
test("docx")   # Test DOCX file conversion
test("all")    # Test all formats
```

## Command Line Interface

### Text Conversion
```bash
# Convert text directly
preeti-unicode text "g]kfn"

# Convert without number conversion
preeti-unicode text "g]kfn @)!&" --no-convert-numbers
```

### File Conversion
```bash
# Convert a single file
preeti-unicode file input.pdf output.txt --output-format txt

# Convert with explicit input format
preeti-unicode file input.pdf output.docx --input-format pdf --output-format docx
```

### Batch Conversion
```bash
# Convert multiple files
preeti-unicode batch *.pdf --input-format pdf --output-format txt --output-dir converted/

# Convert all files in a directory
preeti-unicode batch documents/ --input-format pdf --output-format html --output-dir output/
```

## Testing

The package includes a comprehensive test system that you can use to verify functionality:

```python
from preeti_unicode import test

# Test basic string conversion
test("string")  # Uses default sample text
test("string", "your_preeti_text_here")  # Test with your own text

# Test file format support
test("txt")     # Test TXT file conversion
test("pdf")     # Test PDF file conversion (requires reportlab)
test("docx")    # Test DOCX file conversion (requires python-docx)

# Test everything at once
test("all")     # Comprehensive test of all features
```

## Supported Formats

### Input Formats
- **PDF**: Full support with integrity validation and password protection handling
- **DOCX**: Microsoft Word documents with formatting preservation
- **TXT**: Plain text files with encoding detection

### Output Formats
- **PDF**: Generate Unicode PDF documents
- **DOCX**: Create formatted Word documents
- **TXT**: Plain text output with proper encoding
- **HTML**: Web-ready HTML with proper Unicode rendering

## Contributing

We welcome contributions! Please feel free to submit issues and pull requests.

### Development Setup
```bash
git clone https://github.com/diwaskunwar/preeti-unicode.git
cd preeti-unicode
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

### Running Tests
```bash
# Run the built-in test suite
python -c "from preeti_unicode import test; test('all')"
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/diwaskunwar/preeti-unicode/issues)
- **Documentation**: Check the docstrings and examples in this README

## Acknowledgments

- Thanks to the Nepali computing community for font specifications
- Built with modern Python packaging standards using uv and proper package structure