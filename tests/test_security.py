import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.tools.booking import book_interview

client = TestClient(app)


def test_upload_invalid_chunk_strategy():
    """Verify that an invalid chunking strategy triggers a 400 error."""
    response = client.post(
        "/upload",
        files={"file": ("test.txt", b"some content")},
        data={"chunk_strategy": "invalid_strat"},
    )
    assert response.status_code == 400
    assert "Invalid chunk_strategy" in response.json()["detail"]


def test_upload_invalid_chunk_size_negative():
    """Verify that a negative chunk size is rejected with a 400 error."""
    response = client.post(
        "/upload",
        files={"file": ("test.txt", b"some content")},
        data={"chunk_strategy": "recursive", "chunk_size": -10},
    )
    assert response.status_code == 400
    assert "chunk_size" in response.json()["detail"]


def test_upload_invalid_chunk_size_oversized():
    """Verify that an excessively large chunk size (>10000) is rejected with a 400 error."""
    response = client.post(
        "/upload",
        files={"file": ("test.txt", b"some content")},
        data={"chunk_strategy": "recursive", "chunk_size": 20000},
    )
    assert response.status_code == 400
    assert "chunk_size" in response.json()["detail"]


def test_upload_invalid_overlap_negative():
    """Verify that a negative chunk overlap is rejected with a 400 error."""
    response = client.post(
        "/upload",
        files={"file": ("test.txt", b"some content")},
        data={"chunk_strategy": "recursive", "chunk_overlap": -5},
    )
    assert response.status_code == 400
    assert "chunk_overlap" in response.json()["detail"]


def test_upload_invalid_overlap_too_large():
    """Verify that a chunk overlap greater than or equal to chunk size is rejected with a 400 error."""
    response = client.post(
        "/upload",
        files={"file": ("test.txt", b"some content")},
        data={"chunk_strategy": "recursive", "chunk_size": 100, "chunk_overlap": 150},
    )
    assert response.status_code == 400
    assert "strictly less than chunk_size" in response.json()["detail"].lower()


def test_upload_invalid_percentile_high():
    """Verify that a similarity percentile greater than 100 is rejected with a 400 error."""
    response = client.post(
        "/upload",
        files={"file": ("test.txt", b"some content")},
        data={"chunk_strategy": "semantic", "similarity_percentile": 120.0},
    )
    assert response.status_code == 400
    assert "similarity_percentile" in response.json()["detail"]


def test_upload_invalid_percentile_low():
    """Verify that a negative similarity percentile is rejected with a 400 error."""
    response = client.post(
        "/upload",
        files={"file": ("test.txt", b"some content")},
        data={"chunk_strategy": "semantic", "similarity_percentile": -10.0},
    )
    assert response.status_code == 400
    assert "similarity_percentile" in response.json()["detail"]


def test_upload_oversized_file():
    """Verify that a document payload exceeding the 10MB limit is rejected with a 413 error."""
    # Build a file payload just over 10MB
    large_payload = b"A" * (10 * 1024 * 1024 + 100)
    response = client.post(
        "/upload",
        files={"file": ("large.txt", large_payload)},
        data={"chunk_strategy": "recursive"},
    )
    assert response.status_code == 413
    assert "exceeds maximum upload limit" in response.json()["detail"]


def test_book_interview_tool_email_validation():
    """Verify that the book_interview tool detects malformed emails before processing."""
    res = book_interview.invoke(
        {
            "full_name": "Raj Shriwastava",
            "email": "invalidemail",
            "date": "2026-06-10",
            "time": "11:00 AM",
        }
    )
    assert "Error: The email address" in res


def test_book_interview_tool_name_sanitization():
    """Verify that book_interview strips script elements and rejects empty names."""
    res = book_interview.invoke(
        {
            "full_name": "   <script></script>   ",
            "email": "raj@example.com",
            "date": "2026-06-10",
            "time": "11:00 AM",
        }
    )
    assert "Error: The full name cannot be empty" in res


def test_book_interview_tool_date_validation():
    """Verify that book_interview rejects malformed dates."""
    res = book_interview.invoke(
        {
            "full_name": "Raj Shriwastava",
            "email": "raj@example.com",
            "date": "10/06/2026",
            "time": "11:00 AM",
        }
    )
    assert "Error: The date" in res


def test_book_interview_tool_time_validation():
    """Verify that book_interview rejects malformed times."""
    res = book_interview.invoke(
        {
            "full_name": "Raj Shriwastava",
            "email": "raj@example.com",
            "date": "2026-06-10",
            "time": "morningish",
        }
    )
    assert "Error: The time" in res


def test_chat_oversized_message():
    """Verify that an assistant turn with a payload over 10k characters is rejected."""
    huge_message = "A" * 10005
    response = client.post(
        "/chat", json={"session_id": "test-session", "message": huge_message}
    )
    # Pydantic validation error triggers a 422 Unprocessable Entity response
    assert response.status_code == 422
    assert "message" in response.text


def test_chat_invalid_session_id_characters():
    """Verify that a session ID containing special characters or traversal path segments is rejected."""
    response = client.post(
        "/chat", json={"session_id": "session/../../etc/passwd", "message": "hello"}
    )
    assert response.status_code == 422
    assert "session_id" in response.text


def test_chat_oversized_session_id():
    """Verify that a session ID exceeding the 100-character boundary is rejected."""
    huge_session = "s" * 105
    response = client.post(
        "/chat", json={"session_id": huge_session, "message": "hello"}
    )
    assert response.status_code == 422
    assert "session_id" in response.text


@patch("app.api.upload.IngestionService")
def test_upload_filename_traversal_sanitization(mock_ingestion_class):
    """Verify that file uploads strip out directory traversal patterns, saving only the secure basename."""
    mock_instance = MagicMock()
    mock_ingestion_class.return_value = mock_instance
    mock_instance.ingest_document.return_value = {
        "status": "success",
        "message": "File ingested successfully.",
        "document_id": "11111111-2222-4333-a444-555555555555",
        "strategy_used": "recursive",
        "embedding_model": "Snowflake/snowflake-arctic-embed-m",
        "chunks_count": 1,
        "metadata": {"filename": "passwd.txt"},
    }

    response = client.post(
        "/upload",
        files={"file": ("../../../../etc/passwd.txt", b"some txt content")},
        data={"chunk_strategy": "recursive"},
    )

    assert response.status_code == 201
    # Verify that the IngestionService was indeed called with the secure basename "passwd.txt"
    mock_instance.ingest_document.assert_called_once()
    called_args = mock_instance.ingest_document.call_args[1]
    assert called_args["filename"] == "passwd.txt"
