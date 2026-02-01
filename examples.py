#!/usr/bin/env python3
"""
Advanced PDF Reader - Usage Examples

This script demonstrates all the advanced features of the PDF reader.
"""

from justpdf import justpdf


def example_basic_info(pdf_path):
    """Example: Get basic PDF information"""
    print("EXAMPLE 1: Basic PDF Information")
    
    reader = justpdf(pdf_path)
    info = reader.get_info()
    
    print(f"File: {info['path']}")
    print(f"Total Pages: {info['page_count']}")
    print(f"PDF Objects: {info['object_count']}")
    print(f"Images Found: {info['image_count']}")


def example_metadata(pdf_path):
    """Example: Extract and display metadata"""
    print("EXAMPLE 2: PDF Metadata Extraction")
    
    reader = justpdf(pdf_path)
    metadata = reader.get_metadata()
    
    if metadata:
        for key, value in metadata.items():
            print(f"  {key:15s}: {value}")
    else:
        print("  No metadata available")


def example_page_extraction(pdf_path, page_num=1):
    """Example: Extract text from specific page"""
    print(f"EXAMPLE 3: Extract Text from Page {page_num}")
    
    reader = justpdf(pdf_path)
    
    if page_num > reader.get_page_count():
        print(f"  Error: Page {page_num} doesn't exist")
        return
    
    text = reader.extract_text_from_page(page_num)
    print(f"\n--- Page {page_num} Content ---")
    print(text[:1000])  # Show first 1000 characters
    
    if len(text) > 1000:
        print(f"\n... [truncated, {len(text) - 1000} more characters]")


def example_all_pages(pdf_path):
    """Example: Extract text from all pages"""
    print("EXAMPLE 4: Extract Text from All Pages")    
    reader = justpdf(pdf_path)
    
    for page_num in range(1, reader.get_page_count() + 1):
        text = reader.extract_text_from_page(page_num)
        print(f"\n--- Page {page_num} ({len(text)} characters) ---")
        # Show first 200 characters of each page
        print(text[:200])
        if len(text) > 200:
            print("...")


def example_search(pdf_path, query):
    """Example: Search for text in PDF"""
    print(f"EXAMPLE 5: Search for '{query}'")
    
    reader = justpdf(pdf_path)
    results = reader.search_text(query)
    
    print(f"  Found {len(results)} occurrences\n")
    
    for i, result in enumerate(results[:10], 1):
        print(f"  {i}. Page {result['page']}, Line {result['line']}")
        print(f"     {result['text'][:80]}...")
    
    if len(results) > 10:
        print(f"\n  ... and {len(results) - 10} more results")


def example_images(pdf_path):
    """Example: Extract image information"""
    print("EXAMPLE 6: Image Extraction")
    
    reader = justpdf(pdf_path)
    images = reader.extract_images()
    
    if images:
        print(f"  Found {len(images)} images\n")
        for i, img in enumerate(images, 1):
            print(f"  Image {i}:")
            print(f"    Object ID: {img['obj_id']}")
            print(f"    Size: {img['width']}x{img['height']} pixels")
            print(f"    Colorspace: {img['colorspace']}")
            print(f"    Compression: {img['filter']}")
            print()
    else:
        print("  No images found in PDF")


def example_page_range(pdf_path, start_page, end_page):
    """Example: Extract text from a range of pages"""
    print(f"EXAMPLE 7: Extract Pages {start_page}-{end_page}")
    
    reader = justpdf(pdf_path)
    all_text = []
    
    for page_num in range(start_page, end_page + 1):
        if page_num > reader.get_page_count():
            break
        text = reader.extract_text_from_page(page_num)
        all_text.append(f"--- Page {page_num} ---\n{text}\n")
    
    combined_text = '\n'.join(all_text)
    print(combined_text[:1500])  # Show first 1500 characters
    
    if len(combined_text) > 1500:
        print(f"\n... [truncated, {len(combined_text) - 1500} more characters]")


def example_export_to_file(pdf_path, output_file):
    """Example: Export extracted text to a file"""
    print(f"EXAMPLE 8: Export Text to {output_file}")
    
    reader = justpdf(pdf_path)
    text = reader.extract_text()
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(text)
    
    print(f"Exported {len(text)} characters to {output_file}")


def main():
    """Run all examples"""
    pdf_path = "sample.pdf"
    
    print("justpdf- FEATURE DEMONSTRATIONS")
    
    try:
        # Run examples
        example_basic_info(pdf_path)
        example_metadata(pdf_path)
        example_page_extraction(pdf_path, page_num=1)
        example_search(pdf_path, "python")
        example_images(pdf_path)
        example_page_range(pdf_path, 1, 2)
        example_export_to_file(pdf_path, "extracted_text.txt")
        
        
    except FileNotFoundError:
        print(f"\nError: Could not find '{pdf_path}'")
        print("Please make sure the PDF file exists in the current directory.\n")
    except Exception as e:
        print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()
