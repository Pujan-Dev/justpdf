"""justpdf - a small, dependency-free PDF text extraction library."""

from .errors import PdfError, UnsupportedPdfError
from .reader import Page, PdfReader, read_pdf

__version__ = "0.1.0"
__all__ = ["PdfReader", "Page", "read_pdf", "PdfError", "UnsupportedPdfError"]
