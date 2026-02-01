#!/usr/bin/env python3
"""
PDF Utilities - Command-line tools for PDF operations
"""

import argparse
import sys
from pathlib import Path

from justpdf import justpdf


def info_command(pdf_path):
    """Display PDF information"""
    reader = justpdf(pdf_path)
    info = reader.get_info()
    metadata = reader.get_metadata()
    
    print("\n" + "=" * 70)
    print("PDF INFORMATION")
    print("=" * 70)
    print(f"File: {info['path']}")
    print(f"Pages: {info['page_count']}")
    print(f"Objects: {info['object_count']}")
    print(f"Images: {info['image_count']}")
    
    if metadata:
        print("\nMetadata:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")
    print()


def extract_command(pdf_path, output=None, page=None):
    """Extract text from PDF"""
    reader = justpdf(pdf_path)
    
    if page:
        text = reader.extract_text_from_page(page)
        print(f"Extracting text from page {page}...\n")
    else:
        text = reader.extract_text()
        print(f"Extracting text from all {reader.get_page_count()} pages...\n")
    
    if output:
        with open(output, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"✓ Text saved to {output}")
        print(f"  ({len(text)} characters)")
    else:
        print(text)


def search_command(pdf_path, query, context=0):
    """Search for text in PDF"""
    reader = justpdf(pdf_path)
    results = reader.search_text(query)
    
    print(f"\nSearching for '{query}'...")
    print(f"Found {len(results)} occurrences\n")
    
    if results:
        for i, result in enumerate(results, 1):
            print(f"{i}. Page {result['page']}, Line {result['line']}")
            print(f"   {result['text']}")
            
            if context > 0:
                # Show surrounding lines if requested
                page_text = reader.extract_text_from_page(result['page'])
                lines = page_text.split('\n')
                line_idx = result['line'] - 1
                
                start = max(0, line_idx - context)
                end = min(len(lines), line_idx + context + 1)
                
                if start < line_idx:
                    for j in range(start, line_idx):
                        print(f"     {lines[j]}")
                
                if end > line_idx + 1:
                    for j in range(line_idx + 1, end):
                        print(f"     {lines[j]}")
            print()


def images_command(pdf_path, detailed=False):
    """List images in PDF"""
    reader = justpdf(pdf_path)
    images = reader.extract_images()
    
    print(f"\nFound {len(images)} images in PDF\n")
    
    if images:
        for i, img in enumerate(images, 1):
            print(f"Image {i}:")
            print(f"  Object ID: {img['obj_id']}")
            print(f"  Size: {img['width']}x{img['height']} pixels")
            
            if detailed:
                print(f"  Colorspace: {img['colorspace']}")
                print(f"  Filter: {img['filter']}")
            print()


def pages_command(pdf_path, start=None, end=None):
    """List or extract specific pages"""
    reader = justpdf(pdf_path)
    total_pages = reader.get_page_count()
    
    if start is None and end is None:
        print(f"\nTotal pages: {total_pages}")
        print("\nPage overview:")
        for i in range(1, total_pages + 1):
            text = reader.extract_text_from_page(i)
            char_count = len(text)
            word_count = len(text.split())
            print(f"  Page {i}: {char_count} characters, ~{word_count} words")
        print()
    else:
        start = start or 1
        end = end or total_pages
        
        print(f"\nExtracting pages {start} to {end}...\n")
        for i in range(start, min(end + 1, total_pages + 1)):
            print(f"--- Page {i} ---")
            print(reader.extract_text_from_page(i))
            print()


def main():
    parser = argparse.ArgumentParser(
        description='Advanced PDF Reader - Command-line utilities',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s info document.pdf                    # Show PDF info
  %(prog)s extract document.pdf                 # Extract all text
  %(prog)s extract document.pdf -p 1            # Extract page 1
  %(prog)s extract document.pdf -o output.txt   # Save to file
  %(prog)s search document.pdf "python"         # Search for text
  %(prog)s images document.pdf                  # List images
  %(prog)s pages document.pdf                   # List all pages
  %(prog)s pages document.pdf -s 1 -e 3         # Show pages 1-3
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Display PDF information')
    info_parser.add_argument('pdf', help='PDF file path')
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract text from PDF')
    extract_parser.add_argument('pdf', help='PDF file path')
    extract_parser.add_argument('-p', '--page', type=int, help='Specific page to extract')
    extract_parser.add_argument('-o', '--output', help='Output file path')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for text in PDF')
    search_parser.add_argument('pdf', help='PDF file path')
    search_parser.add_argument('query', help='Text to search for')
    search_parser.add_argument('-c', '--context', type=int, default=0,
                             help='Number of context lines to show')
    
    # Images command
    images_parser = subparsers.add_parser('images', help='List images in PDF')
    images_parser.add_argument('pdf', help='PDF file path')
    images_parser.add_argument('-d', '--detailed', action='store_true',
                             help='Show detailed information')
    
    # Pages command
    pages_parser = subparsers.add_parser('pages', help='List or extract pages')
    pages_parser.add_argument('pdf', help='PDF file path')
    pages_parser.add_argument('-s', '--start', type=int, help='Start page')
    pages_parser.add_argument('-e', '--end', type=int, help='End page')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'info':
            info_command(args.pdf)
        elif args.command == 'extract':
            extract_command(args.pdf, args.output, args.page)
        elif args.command == 'search':
            search_command(args.pdf, args.query, args.context)
        elif args.command == 'images':
            images_command(args.pdf, args.detailed)
        elif args.command == 'pages':
            pages_command(args.pdf, args.start, args.end)
    
    except FileNotFoundError:
        print(f"\n❌ Error: File '{args.pdf}' not found\n", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}\n", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
