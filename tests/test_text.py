from justpdf import text


def test_extract_text_from_tj():
    assert text.extract_text(b"BT (Hello World) Tj ET") == "Hello World"


def test_extract_text_from_tj_array():
    assert text.extract_text(b"BT [(Hello) -250 (World)] TJ ET") == "HelloWorld"


def test_extract_text_from_quote_operators():
    assert text.extract_text(b"(Line one) '\n(Line two) \"") == "Line one Line two"


def test_extract_text_ignores_non_text_operators():
    assert text.extract_text(b"1 0 0 1 0 0 cm\nq\nQ") == ""


def test_decode_literal_string_handles_escapes():
    assert text.decode_literal_string(rb"Hello\nWorld\(x\)") == "Hello\nWorld(x)"


def test_decode_hex_string_utf16be():
    # "Hi" as UTF-16BE
    assert text.decode_hex_string(b"00480069") == "Hi"


def test_decode_hex_string_with_char_map():
    char_map = {0x0030: "A", 0x0044: "B"}
    assert text.decode_hex_string(b"00300044", char_map) == "AB"


def test_single_glyph_per_tj_joins_without_spaces():
    # Some PDFs (e.g. Google Docs exports) show one glyph per Tj call.
    stream = b"BT (H) Tj (i) Tj ET"
    assert text.extract_text(stream) == "Hi"


def test_parse_tounicode_cmap_bfchar():
    cmap = b"1 beginbfchar\n<0041> <0042>\nendbfchar"
    assert text.parse_tounicode_cmap(cmap) == {0x41: "B"}


def test_parse_tounicode_cmap_bfrange():
    cmap = b"1 beginbfrange\n<0041> <0043> <0061>\nendbfrange"
    assert text.parse_tounicode_cmap(cmap) == {0x41: "a", 0x42: "b", 0x43: "c"}
