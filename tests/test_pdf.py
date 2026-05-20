import pytest
from app.utils.pdf import extract_text_from_bytes

def test_extract_text_from_txt_utf8():
    """Verify clean decoding of UTF-8 text file payloads."""
    payload = b"Hello PalmMind AI Core Engineering!"
    result = extract_text_from_bytes(payload, "test.txt")
    assert result == "Hello PalmMind AI Core Engineering!"

def test_extract_text_unsupported_format():
    """Verify that unsupported file extensions trigger ValueError."""
    with pytest.raises(ValueError) as excinfo:
        extract_text_from_bytes(b"dummy binary data", "document.xlsx")
    assert "Unsupported format" in str(excinfo.value)
