import pytest

from justpdf import PdfReader, UnsupportedPdfError, read_pdf
from conftest import SAMPLE_PDF


def test_page_count(pdf_factory):
    path = pdf_factory([b"BT (Hello) Tj ET", b"BT (World) Tj ET"])
    reader = PdfReader(path)
    assert reader.page_count == 2


def test_extract_text_joins_pages(pdf_factory):
    path = pdf_factory([b"BT (Hello) Tj ET", b"BT (World) Tj ET"])
    reader = PdfReader(path)
    assert reader.extract_text() == "Hello\n\nWorld"


def test_individual_page_text(pdf_factory):
    path = pdf_factory([b"BT (Hello) Tj ET", b"BT (World) Tj ET"])
    reader = PdfReader(path)
    assert reader.pages[0].text == "Hello"
    assert reader.pages[1].text == "World"


def test_search_finds_matching_line(pdf_factory):
    path = pdf_factory([b"BT (Hello World) Tj ET"])
    reader = PdfReader(path)
    results = reader.search("world")
    assert results == [{"page": 1, "line": 1, "text": "Hello World"}]


def test_search_is_case_insensitive_by_default(pdf_factory):
    path = pdf_factory([b"BT (Hello World) Tj ET"])
    reader = PdfReader(path)
    assert reader.search("HELLO") != []
    assert reader.search("HELLO", case_sensitive=True) == []


def test_read_pdf_function(pdf_factory):
    path = pdf_factory([b"BT (Hello) Tj ET"])
    assert read_pdf(path) == "Hello"


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        PdfReader(tmp_path / "does-not-exist.pdf")


def test_non_pdf_file_raises(tmp_path):
    path = tmp_path / "not-a-pdf.txt"
    path.write_bytes(b"just some text, not a pdf")
    with pytest.raises(UnsupportedPdfError):
        PdfReader(path)


def test_pdf_with_no_pages_raises(tmp_path):
    path = tmp_path / "empty.pdf"
    path.write_bytes(b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF")
    with pytest.raises(UnsupportedPdfError):
        PdfReader(path)


def test_uncompressed_content_stream(pdf_factory):
    path = pdf_factory([b"BT (Hello) Tj ET"], compress=False)
    reader = PdfReader(path)
    assert reader.extract_text() == "Hello"


def test_metadata(pdf_factory):
    path = pdf_factory([b"BT (Hello) Tj ET"], metadata={"Title": "My Doc"})
    reader = PdfReader(path)
    assert reader.metadata["Title"] == "My Doc"


@pytest.mark.skipif(not SAMPLE_PDF.exists(), reason="sample.pdf not present")
def test_real_world_sample_pdf():
    reader = PdfReader(SAMPLE_PDF)
    assert reader.page_count >= 1
    text = reader.extract_text()
    assert "Machine learning" in text
