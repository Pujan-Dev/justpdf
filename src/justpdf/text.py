"""Turn a PDF content stream into plain text.

Handles the text-showing operators (Tj, TJ, ', ") and the two PDF string
forms: literal strings in parentheses and hex strings in angle brackets.
"""

from __future__ import annotations

import re

_TEXT_SHOW_RE = re.compile(
    rb"\((?P<paren>(?:[^()\\]|\\.)*)\)\s*(?:Tj|'|\")"
    rb"|<(?P<hex>[0-9A-Fa-f\s]*)>\s*Tj"
    rb"|\[(?P<array>(?:[^\[\]\\]|\\.)*)\]\s*TJ",
    re.S,
)
_ARRAY_ITEM_RE = re.compile(rb"\((?:[^()\\]|\\.)*\)|<[0-9A-Fa-f\s]*>")

_ESCAPES = {
    b"n": b"\n",
    b"r": b"\r",
    b"t": b"\t",
    b"b": b"\x08",
    b"f": b"\x0c",
    b"(": b"(",
    b")": b")",
    b"\\": b"\\",
}


def extract_text(content_stream: bytes, char_map: dict[int, str] | None = None) -> str:
    """Extract the text shown by a page's content stream, in stream order.

    Some PDFs (e.g. those exported by Google Docs) show text one glyph per
    `Tj` call rather than a word or line at a time, with the space between
    words shown as its own glyph. Joining every part with a space would
    then put a space between every letter, so: if every part decoded to a
    single character, the parts are concatenated as-is instead.
    """
    parts = [_decode_match(match, char_map) for match in _TEXT_SHOW_RE.finditer(content_stream)]
    parts = [part for part in parts if part]
    if parts and all(len(part) == 1 for part in parts):
        return "".join(parts)
    return " ".join(parts)


def _decode_match(match: re.Match, char_map: dict[int, str] | None) -> str:
    if match.group("paren") is not None:
        return decode_literal_string(match.group("paren"))
    if match.group("hex") is not None:
        return decode_hex_string(match.group("hex"), char_map)
    return _decode_array(match.group("array"), char_map)


def _decode_array(array_content: bytes, char_map: dict[int, str] | None) -> str:
    pieces = []
    for item in _ARRAY_ITEM_RE.finditer(array_content):
        token = item.group()
        if token.startswith(b"("):
            pieces.append(decode_literal_string(token[1:-1]))
        else:
            pieces.append(decode_hex_string(token[1:-1], char_map))
    return "".join(pieces)


def decode_literal_string(raw: bytes) -> str:
    """Decode a PDF literal string, e.g. the bytes inside `(Hello)`."""
    data = _unescape(raw)
    if data.startswith(b"\xfe\xff"):
        return data.decode("utf-16-be", errors="replace")
    for encoding in ("utf-8", "cp1252", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1", errors="replace")


def _unescape(raw: bytes) -> bytes:
    out = bytearray()
    i = 0
    while i < len(raw):
        byte = raw[i]
        if byte == 0x5C and i + 1 < len(raw):  # backslash
            replacement = _ESCAPES.get(raw[i + 1 : i + 2])
            if replacement is not None:
                out += replacement
                i += 2
                continue
        out.append(byte)
        i += 1
    return bytes(out)


def decode_hex_string(hex_bytes: bytes, char_map: dict[int, str] | None = None) -> str:
    """Decode a PDF hex string, e.g. the bytes inside `<48656C6C6F>`.

    If a ToUnicode `char_map` is given, bytes are read as 2-byte character
    codes and looked up in the map (the common case for embedded/subset
    fonts). Otherwise the bytes are assumed to be UTF-16BE, falling back to
    Latin-1.
    """
    hex_str = re.sub(rb"\s+", b"", hex_bytes).decode("ascii", errors="ignore")
    if len(hex_str) % 2:
        hex_str = hex_str[:-1]
    try:
        raw = bytes.fromhex(hex_str)
    except ValueError:
        return ""

    if char_map:
        return "".join(char_map.get(code, "") for code in _as_uint16_codes(raw))

    if len(raw) % 2 == 0:
        try:
            return raw.decode("utf-16-be")
        except UnicodeDecodeError:
            pass
    return raw.decode("latin-1", errors="replace")


def _as_uint16_codes(raw: bytes):
    for i in range(0, len(raw) - 1, 2):
        yield (raw[i] << 8) | raw[i + 1]


_BFCHAR_BLOCK_RE = re.compile(rb"beginbfchar(.*?)endbfchar", re.S)
_BFRANGE_BLOCK_RE = re.compile(rb"beginbfrange(.*?)endbfrange", re.S)
_HEX_PAIR_RE = re.compile(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>")
_HEX_TRIPLE_RE = re.compile(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>")


def parse_tounicode_cmap(data: bytes) -> dict[int, str]:
    """Parse the bfchar/bfrange sections of a /ToUnicode CMap stream."""
    char_map: dict[int, str] = {}

    for block in _BFCHAR_BLOCK_RE.finditer(data):
        for src, dst in _HEX_PAIR_RE.findall(block.group(1)):
            char_map[int(src, 16)] = chr(int(dst, 16))

    for block in _BFRANGE_BLOCK_RE.finditer(data):
        for src_start, src_end, dst_start in _HEX_TRIPLE_RE.findall(block.group(1)):
            start, end, dst = int(src_start, 16), int(src_end, 16), int(dst_start, 16)
            for offset in range(end - start + 1):
                char_map[start + offset] = chr(dst + offset)

    return char_map
