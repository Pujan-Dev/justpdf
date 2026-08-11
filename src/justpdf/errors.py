class PdfError(Exception):
    """Base class for all justpdf errors."""


class UnsupportedPdfError(PdfError):
    """Raised when a PDF uses a structure justpdf cannot parse."""
