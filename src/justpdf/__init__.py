# justpdf/__init__.py
"""
justpdf - Fast PDF Reader
Pandas-style API for easy PDF text extraction
"""

from .reader import PdfReader, PDFPage, read_pdf, read_pdf_info, search_pdf

__version__ = "1.0.0"
__all__ = ["PdfReader", "PDFPage", "read_pdf", "read_pdf_info", "search_pdf"]
