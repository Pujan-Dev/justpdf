"""Public API: PdfReader, Page, and the read_pdf convenience function."""

from __future__ import annotations

from pathlib import Path

from . import parser, text
from .errors import UnsupportedPdfError


class Page:
    """A single PDF page. Text is extracted lazily, on first access."""

    def __init__(self, number: int, content_stream: bytes, char_map: dict[int, str]):
        self.number = number
        self._content_stream = content_stream
        self._char_map = char_map
        self._text: str | None = None

    @property
    def text(self) -> str:
        if self._text is None:
            self._text = text.extract_text(self._content_stream, self._char_map)
        return self._text


class PdfReader:
    """Reads a PDF file and gives access to its pages and text.

    Example:
        reader = PdfReader("document.pdf")
        print(reader.page_count)
        print(reader.pages[0].text)
        print(reader.extract_text())
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        data = self.path.read_bytes()
        if not data.startswith(b"%PDF-"):
            raise UnsupportedPdfError(f"{self.path} does not look like a PDF file")

        self._data = data
        self._objects = parser.find_objects(data)
        self.pages = self._build_pages()

    def _build_pages(self) -> list[Page]:
        cmap_stream = parser.find_tounicode_stream(self._objects)
        char_map = text.parse_tounicode_cmap(cmap_stream) if cmap_stream else {}

        content_streams = parser.find_page_content_streams(self._objects)
        if not content_streams:
            raise UnsupportedPdfError(
                f"No pages found in {self.path}; this PDF structure isn't supported"
            )
        return [
            Page(number, stream, char_map)
            for number, stream in enumerate(content_streams, start=1)
        ]

    @property
    def page_count(self) -> int:
        return len(self.pages)

    @property
    def metadata(self) -> dict[str, str]:
        return parser.find_metadata(self._data, self._objects)

    def extract_text(self) -> str:
        """Extract text from every page, joined with blank lines."""
        return "\n\n".join(page.text for page in self.pages)

    def search(self, query: str, case_sensitive: bool = False) -> list[dict]:
        """Search for `query` line by line, returning page/line/text matches."""
        needle = query if case_sensitive else query.lower()
        results = []
        for page in self.pages:
            lines = page.text.split("\n")
            haystacks = lines if case_sensitive else [line.lower() for line in lines]
            for line_num, (haystack, line) in enumerate(zip(haystacks, lines), start=1):
                if needle in haystack:
                    results.append({"page": page.number, "line": line_num, "text": line})
        return results


def read_pdf(path: str | Path) -> str:
    """Read a PDF and return its extracted text."""
    return PdfReader(path).extract_text()
