"""Low-level PDF parsing: find objects, pages, and content streams.

This is a minimal, regex-based parser. It does not build a full PDF object
graph or support cross-reference streams, object streams, or encryption. It
is good enough for the common case of a PDF written with plain indirect
objects and FlateDecode-compressed content streams.
"""

from __future__ import annotations

import re
import zlib

_OBJECT_RE = re.compile(rb"(\d+)\s+\d+\s+obj")
_STREAM_RE = re.compile(rb"stream\s*\r?\n(.*?)\r?\nendstream", re.S)
_PAGE_TYPE_RE = re.compile(rb"/Type\s*/Page(?!s)")
_CONTENTS_RE = re.compile(rb"/Contents\s+(\d+)\s+\d+\s+R")
_TOUNICODE_RE = re.compile(rb"/ToUnicode\s+(\d+)\s+\d+\s+R")
_INFO_RE = re.compile(rb"/Info\s+(\d+)\s+\d+\s+R")
_METADATA_FIELD_RE = re.compile(rb"/(\w+)\s*\((.*?)\)", re.S)


def find_objects(data: bytes) -> dict[int, bytes]:
    """Map object id -> object body (the bytes between "N 0 obj" and "endobj")."""
    objects: dict[int, bytes] = {}
    for match in _OBJECT_RE.finditer(data):
        end = data.find(b"endobj", match.end())
        if end == -1:
            continue
        objects[int(match.group(1))] = data[match.end() : end]
    return objects


def decompress(stream: bytes) -> bytes:
    """Inflate a FlateDecode stream, returning it unchanged if that fails."""
    try:
        return zlib.decompress(stream)
    except zlib.error:
        return stream


def get_object_stream(objects: dict[int, bytes], obj_id: int) -> bytes:
    """Return the (decompressed, if needed) stream data for an object."""
    body = objects.get(obj_id)
    if body is None:
        return b""
    match = _STREAM_RE.search(body)
    if match is None:
        return b""
    raw = match.group(1)
    if b"/FlateDecode" in body:
        return decompress(raw)
    return raw


def find_page_content_streams(objects: dict[int, bytes]) -> list[bytes]:
    """Return one decompressed content stream per page object found.

    Pages are returned in the order their objects appear in the file, which
    is usually but not always their reading order. Pages whose /Contents is
    an array of streams (rather than a single stream) are not supported;
    such pages are skipped.
    """
    streams = []
    for body in objects.values():
        if not _PAGE_TYPE_RE.search(body):
            continue
        contents_match = _CONTENTS_RE.search(body)
        if contents_match is None:
            continue
        content_id = int(contents_match.group(1))
        streams.append(get_object_stream(objects, content_id))
    return streams


def find_tounicode_stream(objects: dict[int, bytes]) -> bytes | None:
    """Return the first /ToUnicode CMap stream found, if any.

    A PDF can have a different ToUnicode CMap per font. Using only the first
    one found is a simplification that works for the common case of a
    single embedded font but can misdecode text set in other fonts.
    """
    for body in objects.values():
        match = _TOUNICODE_RE.search(body)
        if match is not None:
            return get_object_stream(objects, int(match.group(1)))
    return None


def find_metadata(data: bytes, objects: dict[int, bytes]) -> dict[str, str]:
    """Extract simple string fields (Title, Author, ...) from the /Info dict."""
    info_match = _INFO_RE.search(data)
    if info_match is None:
        return {}
    body = objects.get(int(info_match.group(1)))
    if body is None:
        return {}
    metadata = {}
    for match in _METADATA_FIELD_RE.finditer(body):
        key = match.group(1).decode("latin-1", errors="ignore")
        value = match.group(2).decode("utf-8", errors="ignore")
        metadata[key] = value
    return metadata
