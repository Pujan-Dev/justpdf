import zlib
from pathlib import Path

import pytest

SAMPLE_PDF = Path(__file__).parent.parent / "sample.pdf"


def build_pdf(content_streams: list[bytes], compress: bool = True, metadata: dict[str, str] | None = None) -> bytes:
    """Build a minimal, valid multi-page PDF with the given content streams."""
    objects = []  # list of (id, body_without_wrapper)

    objects.append((1, b"<</Type /Catalog /Pages 2 0 R>>"))

    page_ids = list(range(3, 3 + len(content_streams)))
    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    objects.append((2, f"<</Type /Pages /Kids [{kids}] /Count {len(content_streams)}>>".encode()))

    content_ids = list(range(3 + len(content_streams), 3 + 2 * len(content_streams)))
    for page_id, content_id in zip(page_ids, content_ids):
        objects.append(
            (page_id, f"<</Type /Page /Parent 2 0 R /Contents {content_id} 0 R>>".encode())
        )

    for content_id, stream in zip(content_ids, content_streams):
        data = zlib.compress(stream) if compress else stream
        filt = b"/Filter /FlateDecode " if compress else b""
        body = b"<<" + filt + f"/Length {len(data)}>>\nstream\n".encode() + data + b"\nendstream"
        objects.append((content_id, body))

    next_id = 3 + 2 * len(content_streams)
    if metadata is not None:
        fields = " ".join(f"/{key} ({value})" for key, value in metadata.items())
        objects.append((next_id, f"<<{fields}>>".encode()))
        info_ref = f"/Info {next_id} 0 R "
    else:
        info_ref = ""

    out = bytearray(b"%PDF-1.4\n")
    for obj_id, body in objects:
        out += f"{obj_id} 0 obj\n".encode() + body + b"\nendobj\n"
    out += f"trailer\n<</Root 1 0 R {info_ref}>>\n".encode()
    out += b"%%EOF"
    return bytes(out)


@pytest.fixture
def pdf_factory(tmp_path):
    def _make(content_streams, compress=True, metadata=None, name="test.pdf"):
        data = build_pdf(content_streams, compress=compress, metadata=metadata)
        path = tmp_path / name
        path.write_bytes(data)
        return path

    return _make
