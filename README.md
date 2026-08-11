# justpdf

A small, dependency-free Python library for extracting text from PDF files.

`justpdf` is a regex-based parser, not a full implementation of the PDF
specification. It handles the common case — a PDF with plain indirect
objects and FlateDecode-compressed content streams — well. It does not
handle encrypted PDFs, PDFs built from cross-reference streams / object
streams, or pages with more than one content stream.

## Installation

```bash
pip install justpdf
```

## Quick start

```python
import justpdf

text = justpdf.read_pdf("document.pdf")
```

```python
from justpdf import PdfReader

reader = PdfReader("document.pdf")

print(reader.page_count)
print(reader.pages[0].text)
print(reader.extract_text())
print(reader.metadata)
print(reader.search("keyword"))
```

## API

### `justpdf.read_pdf(path) -> str`

Reads a PDF and returns all of its text, pages joined by a blank line.

### `justpdf.PdfReader(path)`

- `reader.pages` — list of `Page` objects, in file order
- `reader.page_count` — number of pages
- `reader.metadata` — dict of simple `/Info` fields (e.g. `Title`, `Author`)
- `reader.extract_text()` — all pages' text, joined by a blank line
- `reader.search(query, case_sensitive=False)` — list of
  `{"page": int, "line": int, "text": str}` matches, one per matching line

### `justpdf.Page`

- `page.number` — 1-based page number
- `page.text` — the page's extracted text (computed on first access)

### Errors

- `justpdf.PdfError` — base class for library errors
- `justpdf.UnsupportedPdfError` — raised when the file isn't a PDF, or its
  structure isn't one `justpdf` understands (e.g. no pages found)

Reading a missing file raises the standard `FileNotFoundError`.

## Supported features

- Text-showing operators: `Tj`, `TJ`, `'`, `"`
- Literal strings (`(...)`) with basic escape sequences
- Hex strings (`<...>`), including UTF-16BE and `ToUnicode` CMap lookups
- FlateDecode-compressed content streams
- Basic `/Info` metadata (Title, Author, etc.)
- Line-based text search across pages

## Known limitations

- No support for encrypted PDFs.
- No support for cross-reference streams or object streams (i.e. PDFs
  written to the newer, more compact xref format used by some tools).
- A page's `/Contents` must be a single stream, not an array of streams.
- Only the first `/ToUnicode` CMap found in the file is used, so PDFs that
  embed multiple differently-encoded fonts may decode incorrectly for all
  but one of them.
- Page order follows the order objects appear in the file, which is
  usually — but not guaranteed to be — reading order.
- No image extraction, no PDF writing/modification.

If you hit one of these limits, the library raises `UnsupportedPdfError`
or (for the CMap/ordering caveats) may just produce imperfect text rather
than an error.

## Development

```bash
git clone https://github.com/Pujan-Dev/justpdf.git
cd justpdf
pip install -e ".[dev]"
pytest
```

## License

Apache License 2.0. See [LICENSE](LICENSE).
