#!/usr/bin/env python3
"""
justpdf - PDF Reader Examples
Pandas-style API demonstration
"""

import justpdf

# Example PDF file
PDF_FILE = "sample.pdf"

print("justpdf - PDF Reader")

print("1. Simple text extraction (pandas-style)")

text = justpdf.read_pdf(PDF_FILE)
print(f"Extracted {len(text)} characters")
print(f"First 200 chars:\n{text[:200]}...\n")

# Example 2: Read specific pages only
print("2. Extract specific pages")

# Read pages 0, 1, 2 (0-indexed like pandas)
text = justpdf.read_pdf(PDF_FILE, pages=[0, 1])
print(f"Pages 0-1: {len(text)} characters\n")

print("3. Get PDF information")

info = justpdf.read_pdf_info(PDF_FILE)
print(f"File: {info['file_path']}")
print(f"Pages: {info['page_count']}")
print(f"Metadata: {info['metadata']}\n")

# Example 4: Search in PDF (like pandas.DataFrame.query())
print("4. Search for text")

results = justpdf.search_pdf(PDF_FILE, "python")
print(f"Found {len(results)} results for 'python'")
for r in results[:3]:  # Show first 3
    print(f"  Page {r['page']}, Line {r['line']}: {r['text'][:60]}...")
print()

# Example 5: Using PdfReader class (PyPDF2-style)
print("5. Using PdfReader class")
print("-" * 60)

reader = justpdf.PdfReader(PDF_FILE)
print(f"Total pages: {reader.page_count}")
print(f"Metadata: {reader.metadata}")

# Access individual pages (like PyPDF2)
print(f"\nFirst page text (first 150 chars):")
print(reader.pages[0].text[:150])
print()

# Example 6: Extract text from all pages with reader
print("6. Extract all text with PdfReader")
print("-" * 60)

all_text = reader.extract_text()
print(f"Total text: {len(all_text)} characters")
print(f"Preview:\n{all_text[:200]}...\n")

# Example 7: Search with PdfReader
print("7. Search with case-sensitivity")
print("-" * 60)

# Case-insensitive (default)
results = reader.search("PDF")
print(f"Case-insensitive search for 'PDF': {len(results)} results")

# Case-sensitive
results = reader.search("PDF", case_sensitive=True)
print(f"Case-sensitive search for 'PDF': {len(results)} results\n")

# Example 8: Performance comparison
print("8. Performance test")
print("-" * 60)

import time

# Test 1: pandas-style (one-liner)
start = time.time()
text1 = justpdf.read_pdf(PDF_FILE)
time1 = time.time() - start

# Test 2: Using reader (with caching)
start = time.time()
reader = justpdf.PdfReader(PDF_FILE)
text2 = reader.extract_text()
time2 = time.time() - start

# Test 3: Re-extract (should use cache)
start = time.time()
text3 = reader.extract_text()
time3 = time.time() - start

print(f"Pandas-style: {time1*1000:.2f}ms")
print(f"PdfReader:    {time2*1000:.2f}ms")
print(f"Cached:       {time3*1000:.2f}ms (cached!)")
print()

print("=" * 60)
print("All examples completed successfully!")
print("=" * 60)
