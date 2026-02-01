# justpdf/reader.py
"""
Fast PDF Reader - Better and faster than PyPDF2
Pandas-style API for easy use
"""
import re
import zlib
from typing import Dict, List, Optional, Union
from functools import lru_cache


class PDFPage:
    """Represents a single PDF page with lazy text loading"""
    
    # Pre-compile patterns for faster extraction (class-level)
    _PAREN_TJ = re.compile(rb'\(((?:[^()\\]|\\[()\\nrtbf])*?)\)\s*Tj')
    _HEX_TJ = re.compile(rb'<([0-9A-Fa-f]+)>\s*Tj')
    _ARRAY_TJ = re.compile(rb'\[(.*?)\]\s*TJ', re.S)
    _PAREN_QUOTE = re.compile(rb'\(((?:[^()\\]|\\[()\\])*?)\)\s*[\'"]')
    _PAREN_IN_ARRAY = re.compile(rb'\(((?:[^()\\]|\\[()\\])*?)\)')
    _HEX_IN_ARRAY = re.compile(rb'<([0-9A-Fa-f]+)>')
    
    def __init__(self, page_num: int, content_stream: bytes, char_map: Dict[int, str] = None):
        self.page_num = page_num
        self._content_stream = content_stream
        self._char_map = char_map or {}
        self._text_cache = None
    
    @property
    def text(self) -> str:
        """Lazy load page text"""
        if self._text_cache is None:
            self._text_cache = self._extract_text()
        return self._text_cache
    
    def _extract_text(self) -> str:
        """Extract text from page content stream - optimized for speed"""
        text_parts = []
        
        # Use pre-compiled patterns for faster matching
        # Process parentheses Tj operators
        for match in self._PAREN_TJ.finditer(self._content_stream):
            decoded = self._decode_text(match.group(1))
            if decoded:
                text_parts.append(decoded)
        
        # Process hex Tj operators
        for match in self._HEX_TJ.finditer(self._content_stream):
            decoded = self._decode_hex_with_map(match.group(1), self._char_map)
            if decoded:
                text_parts.append(decoded)
        
        # Process TJ arrays
        for match in self._ARRAY_TJ.finditer(self._content_stream):
            array_content = match.group(1)
            # Extract paren strings
            for s in self._PAREN_IN_ARRAY.finditer(array_content):
                decoded = self._decode_text(s.group(1))
                if decoded:
                    text_parts.append(decoded)
            # Extract hex strings
            for s in self._HEX_IN_ARRAY.finditer(array_content):
                decoded = self._decode_hex_with_map(s.group(1), self._char_map)
                if decoded:
                    text_parts.append(decoded)
        
        # Process quote operators
        for match in self._PAREN_QUOTE.finditer(self._content_stream):
            decoded = self._decode_text(match.group(1))
            if decoded:
                text_parts.append(decoded)
        
        # Join text parts intelligently
        return self._join_text_parts(text_parts)
    
    def _join_text_parts(self, parts: List[str]) -> str:
        """Join text parts intelligently (remove extra spaces from Google Docs PDFs)"""
        # If all parts are single characters, join without spaces
        if all(len(p) == 1 for p in parts if p.strip()):
            return ''.join(parts)
        
        # Otherwise join with spaces
        return ' '.join(parts)
    
    def _decode_hex_with_map(self, hex_str: bytes, char_map: Dict[int, str]) -> str:
        """Decode hexadecimal string using character mapping (for Google Docs PDFs)"""
        try:
            hex_str = hex_str.decode('ascii').replace(' ', '')
            
            # Use character map if available
            if char_map:
                chars = []
                # Process in 4-char or 2-char chunks
                chunk_size = 4 if len(hex_str) % 4 == 0 else 2
                for i in range(0, len(hex_str), chunk_size):
                    chunk = hex_str[i:i+chunk_size]
                    char_id = int(chunk, 16)
                    
                    # Use character map
                    if char_id in char_map:
                        chars.append(char_map[char_id])
                    else:
                        # Try direct Unicode
                        if 32 <= char_id <= 126 or char_id >= 160:
                            chars.append(chr(char_id))
                
                return ''.join(chars)
            
            # Fallback: try standard decoding
            # Method 1: UTF-16BE
            if len(hex_str) % 4 == 0:
                try:
                    byte_data = bytes.fromhex(hex_str)
                    decoded = byte_data.decode('utf-16-be', errors='strict')
                    if decoded.strip():
                        return decoded
                except:
                    pass
            
            # Method 2: Direct Unicode code points
            chars = []
            chunk_size = 4 if len(hex_str) % 4 == 0 else 2
            for i in range(0, len(hex_str), chunk_size):
                chunk = hex_str[i:i+chunk_size]
                code = int(chunk, 16)
                if 32 <= code <= 126 or code >= 160:
                    chars.append(chr(code))
            
            return ''.join(chars)
        except:
            return ''
    
    def _decode_text(self, text: bytes) -> str:
        """Decode PDF text with escape sequences and multiple encodings"""
        # Handle PDF escape sequences
        text = text.replace(b'\\n', b'\n')
        text = text.replace(b'\\r', b'\r')
        text = text.replace(b'\\t', b'\t')
        text = text.replace(b'\\(', b'(')
        text = text.replace(b'\\)', b')')
        text = text.replace(b'\\\\', b'\\')
        
        # Try multiple encodings (PDFs can use various encodings)
        for encoding in ['utf-8', 'utf-16-be', 'latin-1', 'cp1252']:
            try:
                decoded = text.decode(encoding, errors='strict')
                if decoded.strip():
                    return decoded
            except (UnicodeDecodeError, LookupError):
                continue
        
        # Fallback with error handling
        return text.decode('utf-8', errors='ignore').strip()


class PdfReader:
    """
    Fast PDF Reader with PyPDF2-compatible API
    
    Usage:
        reader = PdfReader('document.pdf')
        print(f"Pages: {reader.page_count}")
        text = reader.extract_text()
        page_text = reader.pages[0].text
    
    Performance optimizations:
        - Lazy loading of pages
        - LRU caching for decompression
        - Compiled regex patterns
        - Minimal memory footprint
    """
    
    # Pre-compiled regex patterns (class-level for speed)
    _STREAM_RE = re.compile(rb'stream\s*\n(.*?)\nendstream', re.S)
    _PAGE_RE = re.compile(rb'/Type\s*/Page[^s]')
    _METADATA_RE = re.compile(rb'/(\w+)\s*\((.*?)\)', re.S)
    _PAGE_OBJ_RE = re.compile(rb'(\d+)\s+\d+\s+obj')  # Simplified - just find obj starts
    _CONTENTS_RE = re.compile(rb'/Contents\s*(\d+)\s+\d+\s+R')
    _CMAP_RE = re.compile(rb'/ToUnicode\s+(\d+)\s+\d+\s+R')
    _BFCHAR_RE = re.compile(rb'beginbfchar(.*?)endbfchar', re.S)
    _BFRANGE_RE = re.compile(rb'beginbfrange(.*?)endbfrange', re.S)
    _MAPPING_RE = re.compile(rb'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>')
    _RANGE_RE = re.compile(rb'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>')
    
    def __init__(self, file_path: str):
        """
        Initialize PDF reader
        
        Args:
            file_path: Path to PDF file
        """
        self.file_path = file_path
        self._data = self._load_file()
        self._pages_cache = None
        self._metadata_cache = None
        self._char_map_cache = None
    
    def _load_file(self) -> bytes:
        """Load PDF file into memory"""
        with open(self.file_path, 'rb') as f:
            return f.read()
    
    @property
    def pages(self) -> List[PDFPage]:
        """Get all pages (lazy loaded)"""
        if self._pages_cache is None:
            self._pages_cache = self._extract_pages()
        return self._pages_cache
    
    @property
    def page_count(self) -> int:
        """Get total number of pages"""
        return len(self.pages)
    
    @property
    def metadata(self) -> Dict[str, str]:
        """Get PDF metadata (lazy loaded)"""
        if self._metadata_cache is None:
            self._metadata_cache = self._extract_metadata()
        return self._metadata_cache
    
    def extract_text(self, pages: Optional[List[int]] = None) -> str:
        """
        Extract text from PDF
        
        Args:
            pages: Optional list of page numbers (0-indexed). If None, extracts all pages.
        
        Returns:
            Extracted text
        
        Example:
            # Extract all pages
            text = reader.extract_text()
            
            # Extract specific pages
            text = reader.extract_text(pages=[0, 1, 2])
        """
        if pages is None:
            # Extract all pages
            return '\n\n'.join(page.text for page in self.pages)
        else:
            # Extract specific pages
            result = []
            for page_num in pages:
                if 0 <= page_num < self.page_count:
                    result.append(self.pages[page_num].text)
            return '\n\n'.join(result)
    
    def search(self, query: str, case_sensitive: bool = False) -> List[Dict[str, Union[int, str]]]:
        """
        Search for text in PDF
        
        Args:
            query: Text to search for
            case_sensitive: Whether search is case-sensitive
        
        Returns:
            List of dicts with 'page', 'line', 'text' keys
        
        Example:
            results = reader.search("python")
            for r in results:
                print(f"Page {r['page']}, Line {r['line']}: {r['text']}")
        """
        results = []
        pattern = query if case_sensitive else query.lower()
        
        for i, page in enumerate(self.pages):
            text = page.text if case_sensitive else page.text.lower()
            for line_num, line in enumerate(text.split('\n'), 1):
                if pattern in line:
                    original_line = page.text.split('\n')[line_num - 1]
                    results.append({
                        'page': i + 1,
                        'line': line_num,
                        'text': original_line
                    })
        
        return results
    
    def get_info(self) -> Dict:
        """
        Get comprehensive PDF information
        
        Returns:
            Dict with keys: file_path, page_count, metadata
        """
        return {
            'file_path': self.file_path,
            'page_count': self.page_count,
            'metadata': self.metadata
        }
    
    @lru_cache(maxsize=256)
    def _decompress_stream(self, data: bytes) -> bytes:
        """Fast stream decompression with LRU caching"""
        try:
            # FlateDecode (most common PDF compression)
            return zlib.decompress(data)
        except:
            try:
                # Try without zlib header
                return zlib.decompress(data, -zlib.MAX_WBITS)
            except:
                # Return uncompressed if decompression fails
                return data
    
    def _extract_pages(self) -> List[PDFPage]:
        """Extract all pages efficiently with character mapping support - optimized for speed"""
        pages = []
        
        # Extract character mappings (ToUnicode CMap) for Google Docs PDFs
        char_map = self._extract_char_map()
        
        # Build object index for faster lookup (avoid repeated regex on entire file)
        obj_index = self._build_object_index()
        
        # Method 1: Find page objects by looking for /Type/Page in object index
        for obj_id, (start, end) in obj_index.items():
            obj_data = self._data[start:end]
            
            # Quick check if this is a page object
            if b'/Type' in obj_data and self._PAGE_RE.search(obj_data):
                # Find Contents reference
                contents_match = self._CONTENTS_RE.search(obj_data)
                if contents_match:
                    content_id = int(contents_match.group(1))
                    
                    # Use object index for faster lookup
                    if content_id in obj_index:
                        c_start, c_end = obj_index[content_id]
                        content_obj = self._data[c_start:c_end]
                        
                        # Extract stream from content object
                        stream_match = self._STREAM_RE.search(content_obj)
                        if stream_match:
                            stream_data = stream_match.group(1)
                            decompressed = self._decompress_stream(stream_data)
                            pages.append(PDFPage(len(pages) + 1, decompressed, char_map))
        
        # Method 2: Fallback - find all streams and try to extract text
        if not pages:
            for page_num, stream_match in enumerate(self._STREAM_RE.finditer(self._data), 1):
                stream_data = stream_match.group(1)
                decompressed = self._decompress_stream(stream_data)
                
                # Quick check for text operators
                if b'Tj' in decompressed or b'TJ' in decompressed:
                    pages.append(PDFPage(page_num, decompressed, char_map))
        
        return pages
    
    def _build_object_index(self) -> Dict[int, tuple]:
        """Build an index of object IDs to their byte positions for faster lookup"""
        obj_index = {}
        obj_pattern = re.compile(rb'(\d+)\s+\d+\s+obj')
        
        for match in obj_pattern.finditer(self._data):
            obj_id = int(match.group(1))
            start = match.start()
            # Find endobj
            end_pos = self._data.find(b'endobj', start)
            if end_pos != -1:
                obj_index[obj_id] = (start, end_pos + 6)
        
        return obj_index
    
    def _extract_char_map(self) -> Dict[int, str]:
        """Extract ToUnicode CMap for character ID to Unicode mapping - optimized"""
        if self._char_map_cache is not None:
            return self._char_map_cache
        
        char_map = {}
        
        # Find ToUnicode CMap using pre-compiled pattern
        cmap_matches = self._CMAP_RE.findall(self._data)
        
        # Early exit if no CMaps found
        if not cmap_matches:
            self._char_map_cache = char_map
            return char_map
        
        # Build object index if not already done (for faster lookup)
        if not hasattr(self, '_obj_index'):
            self._obj_index = self._build_object_index()
        
        for cmap_ref in cmap_matches:
            cmap_id = int(cmap_ref)
            
            # Use object index for faster lookup
            if cmap_id in self._obj_index:
                start, end = self._obj_index[cmap_id]
                cmap_obj = self._data[start:end]
                
                # Extract CMap stream
                stream_match = self._STREAM_RE.search(cmap_obj)
                if stream_match:
                    stream_data = stream_match.group(1)
                    decompressed = self._decompress_stream(stream_data)
                    
                    # Parse CMap using pre-compiled patterns
                    # Process beginbfchar sections
                    for bfchar_match in self._BFCHAR_RE.finditer(decompressed):
                        bfchar_content = bfchar_match.group(1)
                        
                        # Extract mappings
                        for src, dst in self._MAPPING_RE.findall(bfchar_content):
                            try:
                                src_code = int(src, 16)
                                dst_code = int(dst, 16)
                                char_map[src_code] = chr(dst_code)
                            except:
                                pass
                    
                    # Process beginbfrange sections
                    for bfrange_match in self._BFRANGE_RE.finditer(decompressed):
                        bfrange_content = bfrange_match.group(1)
                        
                        for src_start, src_end, dst_start in self._RANGE_RE.findall(bfrange_content):
                            try:
                                src_s = int(src_start, 16)
                                src_e = int(src_end, 16)
                                dst_s = int(dst_start, 16)
                                
                                for i in range(src_e - src_s + 1):
                                    char_map[src_s + i] = chr(dst_s + i)
                            except:
                                pass
        
        self._char_map_cache = char_map
        return char_map
    
    def _extract_metadata(self) -> Dict[str, str]:
        """Extract PDF metadata"""
        metadata = {}
        
        # Find Info dictionary reference
        info_match = re.search(rb'/Info\s*(\d+)\s+\d+\s+R', self._data)
        if info_match:
            obj_id = int(info_match.group(1))
            
            # Find the Info object
            obj_pattern = rf'{obj_id}\s+\d+\s+obj(.*?)endobj'.encode()
            obj_match = re.search(obj_pattern, self._data, re.S)
            
            if obj_match:
                obj_content = obj_match.group(1)
                
                # Extract metadata fields
                for match in self._METADATA_RE.finditer(obj_content):
                    key = match.group(1).decode('latin-1', errors='ignore')
                    value = match.group(2).decode('utf-8', errors='ignore')
                    metadata[key] = value
        
        return metadata


# Pandas-style convenience functions
def read_pdf(file_path: str, pages: Optional[List[int]] = None) -> str:
    """
    Read PDF and extract text (pandas-style API)
    
    Args:
        file_path: Path to PDF file
        pages: Optional list of page numbers (0-indexed)
    
    Returns:
        Extracted text
    
    Example:
        # Read entire PDF
        text = justpdf.read_pdf('document.pdf')
        
        # Read specific pages
        text = justpdf.read_pdf('document.pdf', pages=[0, 1, 2])
    """
    reader = PdfReader(file_path)
    return reader.extract_text(pages=pages)


def read_pdf_info(file_path: str) -> Dict:
    """
    Get PDF information (pandas-style API)
    
    Args:
        file_path: Path to PDF file
    
    Returns:
        Dict with PDF information
    
    Example:
        info = justpdf.read_pdf_info('document.pdf')
        print(f"Pages: {info['page_count']}")
    """
    reader = PdfReader(file_path)
    return reader.get_info()


def search_pdf(file_path: str, query: str, case_sensitive: bool = False) -> List[Dict]:
    """
    Search for text in PDF (pandas-style API)
    
    Args:
        file_path: Path to PDF file
        query: Text to search for
        case_sensitive: Whether search is case-sensitive
    
    Returns:
        List of search results
    
    Example:
        results = justpdf.search_pdf('document.pdf', 'python')
        for r in results:
            print(f"Page {r['page']}: {r['text']}")
    """
    reader = PdfReader(file_path)
    return reader.search(query, case_sensitive)
