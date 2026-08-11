import zlib

from justpdf import parser
from conftest import build_pdf


def test_find_objects():
    data = build_pdf([b"BT (Hi) Tj ET"])
    objects = parser.find_objects(data)
    assert 1 in objects
    assert b"/Catalog" in objects[1]


def test_decompress_flate_stream():
    original = b"BT (Hi) Tj ET"
    compressed = zlib.compress(original)
    assert parser.decompress(compressed) == original


def test_decompress_returns_input_when_not_compressed():
    data = b"not actually compressed"
    assert parser.decompress(data) == data


def test_find_page_content_streams():
    data = build_pdf([b"BT (Hello) Tj ET", b"BT (World) Tj ET"])
    objects = parser.find_objects(data)
    streams = parser.find_page_content_streams(objects)
    assert streams == [b"BT (Hello) Tj ET", b"BT (World) Tj ET"]


def test_find_page_content_streams_uncompressed():
    data = build_pdf([b"BT (Hello) Tj ET"], compress=False)
    objects = parser.find_objects(data)
    assert parser.find_page_content_streams(objects) == [b"BT (Hello) Tj ET"]


def test_find_metadata():
    data = build_pdf([b"BT (Hi) Tj ET"], metadata={"Title": "Report", "Author": "Ada"})
    objects = parser.find_objects(data)
    metadata = parser.find_metadata(data, objects)
    assert metadata == {"Title": "Report", "Author": "Ada"}


def test_find_metadata_returns_empty_dict_without_info():
    data = build_pdf([b"BT (Hi) Tj ET"])
    objects = parser.find_objects(data)
    assert parser.find_metadata(data, objects) == {}
