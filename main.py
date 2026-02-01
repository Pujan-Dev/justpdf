#!/usr/bin/env python3
"""
Main demo for justpdf - Fast PDF Reader
"""

import justpdf

def main():
    PDF_FILE = "sample.pdf"
    
    print(" justpdf - Fast PDF Reader (Better than PyPDF2!)")
    print()
    
    # Pandas-style API - Simple one-liner!
    print("Reading PDF with pandas-style API:")
    
    # Just like pd.read_csv() - super simple!
    text = justpdf.read_pdf(PDF_FILE)
    print(f"✓ Extracted {len(text)} characters")
    print(f"\nFirst 300 characters:\n{text[:300]}...")
    print()
    
    print("PDF Information:")
    info = justpdf.read_pdf_info(PDF_FILE)
    print(f"File:  {info['file_path']}")
    print(f"Pages: {info['page_count']}")
    if info['metadata']:
        print("Metadata:")
        for key, value in info['metadata'].items():
            print(f"  {key}: {value}")
    print()
    
    # Search
    print("Searching for 'PDF':")
    results = justpdf.search_pdf(PDF_FILE, "PDF")
    print(f"Found {len(results)} results")
    for r in results[:5]:  # Show first 5
        print(f"  Page {r['page']}, Line {r['line']}: {r['text'][:60]}...")
    print()
    
    # Using PdfReader class (PyPDF2-compatible)
    print("Using PdfReader class :")
    reader = justpdf.PdfReader(PDF_FILE)
    print(f"Pages: {reader.page_count}")
    print(f"\nFirst page preview:\n{reader.pages[0].text[:250]}...")
    print()
    
    print("All operations completed successfully!")

if __name__ == "__main__":
    main()
