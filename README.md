# justpdf - PDF Reader

A lightweight, high-performance PDF text extraction library with a pandas-style API.

## Features

- **Pandas-style API** - Simple one-liners like `justpdf.read_pdf('file.pdf')`
- **Zero dependencies** - Pure Python with stdlib only
- **High performance** - LRU caching, lazy loading, optimized regex
- **PyPDF2-compatible** - Easy migration from PyPDF2
- **Google Docs PDFs** - Full support for Google Docs exported PDFs with ToUnicode CMap parsing
- **Clean API** - Intuitive and simple to use

## Installation


Install from PyPI:

```
pip install justpdf
```

Or clone this repo:
```
git clone https://github.com/Pujan-Dev/justpdf.git
cd justpdf
```
## Quick Start

### Pandas-style API (Recommended)

```python
import justpdf

# Read entire PDF (like pd.read_csv)
text = justpdf.read_pdf('document.pdf')

# Read specific pages (0-indexed)
text = justpdf.read_pdf('document.pdf', pages=[0, 1, 2])

# Get PDF info
info = justpdf.read_pdf_info('document.pdf')
print(f"Pages: {info['page_count']}")

# Search for text
results = justpdf.search_pdf('document.pdf', 'keyword')
for r in results:
    print(f"Page {r['page']}: {r['text']}")
```

### PyPDF2-style API

```python
import justpdf

# Create reader
reader = justpdf.PdfReader('document.pdf')

# Get page count
print(f"Pages: {reader.page_count}")

# Extract text
text = reader.extract_text()

# Access individual pages
page_text = reader.pages[0].text

# Search
results = reader.search('keyword')

# Get metadata
print(reader.metadata)
```

## API Reference

### Pandas-style Functions

#### `read_pdf(file_path, pages=None)`
Extract text from PDF.

**Args:**
- `file_path` (str): Path to PDF file
- `pages` (list, optional): List of page numbers (0-indexed)

**Returns:** Extracted text as string

**Example:**
```python
# All pages
text = justpdf.read_pdf('doc.pdf')

# Specific pages
text = justpdf.read_pdf('doc.pdf', pages=[0, 2, 4])
```

#### `read_pdf_info(file_path)`
Get PDF information.

**Returns:** Dict with `file_path`, `page_count`, `metadata`

#### `search_pdf(file_path, query, case_sensitive=False)`
Search for text in PDF.

**Returns:** List of dicts with `page`, `line`, `text` keys

### PdfReader Class

#### `PdfReader(file_path)`
Initialize PDF reader.

**Properties:**
- `pages` - List of PDFPage objects
- `page_count` - Number of pages
- `metadata` - PDF metadata dict

**Methods:**
- `extract_text(pages=None)` - Extract text
- `search(query, case_sensitive=False)` - Search text
- `get_info()` - Get PDF info

## Performance

justpdf is optimized for speed with multiple techniques:

- **Object indexing** - O(1) object lookup instead of O(n) regex searches
- **Pre-compiled patterns** - Regex patterns compiled once at class level
- **LRU caching** - Decompressed streams cached (256 entry cache)
- **Lazy loading** - Pages load only when accessed
- **Quick checks** - Fast byte searches before expensive regex

**Benchmark:** 704-page PDF (598K characters):
- Initial load: 1.4ms
- Page extraction: 21ms/page
- Total extraction: ~15s (all 704 pages)
- Cached access: 0ms (instant!)
- Re-extract: 0.2ms (all pages cached)

**Comparison:** Small PDF (1 page):
- justpdf: 3ms
- PyPDF2: 10ms
- **3x faster!**


## Examples

See [demo.py](demo.py) for comprehensive examples:

```bash
python demo.py
```

Or try the quick demo:

```bash
python main.py
```

## Supported Features

✅ Text extraction (Tj, TJ, ', " operators)  
✅ Hex-encoded strings (<hex> format)  
✅ **Google Docs PDFs** (ToUnicode CMap parsing)  
✅ Multiple encodings (UTF-8, UTF-16, Latin-1, CP1252)  
✅ FlateDecode compression  
✅ Metadata extraction  
✅ Text search  
✅ Page-by-page access  

❌ Encrypted PDFs (not supported)  
❌ Image extraction (metadata only)  
❌ PDF writing/modification  

**Note:** Fully supports Google Docs exported PDFs with custom font encodings via ToUnicode CMap parsing.

## Requirements

- Python 3.11+
- No external dependencies!

## License

Open source - free to use and modify under the Apache License 2.0.

## Why justpdf?

**Simple:** Clean API like pandas - `justpdf.read_pdf('file.pdf')`  
**Fast:** Optimized with caching and lazy loading  
**Lightweight:** Zero dependencies, pure Python  
**Compatible:** PyPDF2-style API for easy migration  

Perfect for:
- Text extraction from PDFs
- PDF content analysis
- Document processing pipelines
- Data extraction workflows

---
Made with ❤️ by [Pujan Neupane](https://github.com/Pujan-Dev) — Fast, simple, and powerful PDF reading for Python.
