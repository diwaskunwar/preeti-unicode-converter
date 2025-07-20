"""
Command-line interface for the Preeti Unicode converter.

This module provides a command-line interface for converting files and text
from Preeti font to Unicode.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from preeti_unicode import __version__
from preeti_unicode.converter import convert_text
from preeti_unicode.file_converter import file_converter


def convert_text_command(args) -> int:
    """Handle text conversion command."""
    try:
        result = convert_text(args.text, convert_numbers=args.convert_numbers)
        print(result)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def convert_file_command(args) -> int:
    """Handle file conversion command."""
    try:
        # Auto-detect input format if not specified
        input_format = args.input_format
        if input_format is None:
            from pathlib import Path
            input_path = Path(args.input)
            extension = input_path.suffix.lower()
            if extension == '.pdf':
                input_format = 'pdf'
            elif extension in ['.docx', '.doc']:
                input_format = 'docx'
            elif extension in ['.txt', '.text']:
                input_format = 'txt'
            else:
                print(f"Error: Cannot auto-detect format for file: {args.input}", file=sys.stderr)
                return 1

        success = file_converter(
            input_file=args.input,
            input_format=input_format,
            output_file=args.output,
            output_format=args.output_format,
            convert_numbers=args.convert_numbers
        )
        
        if success:
            print(f"Successfully converted {args.input} to {args.output}")
            return 0
        else:
            print(f"Failed to convert {args.input}", file=sys.stderr)
            return 1
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def batch_convert_command(args) -> int:
    """Handle batch conversion command."""
    try:
        from .file_converter import _file_converter
        
        # Get list of input files
        input_files = []
        for pattern in args.input_files:
            path = Path(pattern)
            if path.is_file():
                input_files.append(path)
            elif path.is_dir():
                # Find files with matching extension
                extension = f".{args.input_format}"
                input_files.extend(path.glob(f"*{extension}"))
            else:
                # Try glob pattern
                input_files.extend(Path('.').glob(pattern))
        
        if not input_files:
            print("No input files found", file=sys.stderr)
            return 1
        
        print(f"Found {len(input_files)} files to convert")
        
        results = _file_converter.batch_convert(
            input_files=input_files,
            input_format=args.input_format,
            output_dir=args.output_dir,
            output_format=args.output_format,
            convert_numbers=args.convert_numbers
        )
        
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        
        print(f"Conversion completed: {successful}/{total} files successful")
        
        if successful < total:
            print("Failed files:")
            for file_path, success in results.items():
                if not success:
                    print(f"  - {file_path}")
        
        return 0 if successful == total else 1
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog='preeti-unicode',
        description='Convert Preeti font text to Unicode (Nepali)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert text directly
  preeti-unicode text "k]jL"
  
  # Convert a PDF file to text
  preeti-unicode file input.pdf output.txt --input-format pdf --output-format txt
  
  # Convert multiple files
  preeti-unicode batch *.pdf --input-format pdf --output-format txt --output-dir converted/
  
  # Convert without number conversion
  preeti-unicode file input.pdf output.txt --input-format pdf --output-format txt --no-convert-numbers
"""
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    parser.add_argument(
        '--no-convert-numbers',
        dest='convert_numbers',
        action='store_false',
        help='Do not convert English numerals to Nepali numerals'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Text conversion command
    text_parser = subparsers.add_parser(
        'text',
        help='Convert text directly'
    )
    text_parser.add_argument(
        'text',
        help='Preeti text to convert'
    )
    text_parser.set_defaults(func=convert_text_command)
    
    # File conversion command
    file_parser = subparsers.add_parser(
        'file',
        help='Convert a single file'
    )
    file_parser.add_argument(
        'input',
        help='Input file path'
    )
    file_parser.add_argument(
        'output',
        help='Output file path'
    )
    file_parser.add_argument(
        '--input-format',
        choices=['pdf', 'docx', 'txt'],
        help='Input file format (auto-detected if not specified)'
    )
    file_parser.add_argument(
        '--output-format',
        choices=['pdf', 'docx', 'txt', 'html'],
        required=True,
        help='Output file format'
    )
    file_parser.set_defaults(func=convert_file_command)
    
    # Batch conversion command
    batch_parser = subparsers.add_parser(
        'batch',
        help='Convert multiple files'
    )
    batch_parser.add_argument(
        'input_files',
        nargs='+',
        help='Input file patterns or directories'
    )
    batch_parser.add_argument(
        '--input-format',
        choices=['pdf', 'docx', 'txt'],
        required=True,
        help='Input file format'
    )
    batch_parser.add_argument(
        '--output-format',
        choices=['pdf', 'docx', 'txt', 'html'],
        required=True,
        help='Output file format'
    )
    batch_parser.add_argument(
        '--output-dir',
        default='converted',
        help='Output directory (default: converted)'
    )
    batch_parser.set_defaults(func=batch_convert_command)
    
    return parser


def main() -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not hasattr(args, 'func'):
        # No subcommand provided, show help
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
