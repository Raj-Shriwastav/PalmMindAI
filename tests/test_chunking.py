import pytest
from app.utils.chunking import RecursiveCharacterChunker


def test_recursive_character_chunker_basic():
    """Verify that recursive character chunking splits text within bounds."""
    chunk_size = 80
    chunk_overlap = 10
    chunker = RecursiveCharacterChunker(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )

    text = (
        "PalmMind AI is a privacy-first engineering platform. "
        "We prioritize clean separation of concerns and robust TDD patterns. "
        "This ensures maximum reliability."
    )

    chunks = chunker.chunk_text(text)

    assert len(chunks) >= 1
    for chunk in chunks:
        assert len(chunk) <= chunk_size
        assert len(chunk) > 0


def test_recursive_character_chunker_empty():
    """Verify that chunking empty text returns an empty list."""
    chunker = RecursiveCharacterChunker()
    assert chunker.chunk_text("") == []
