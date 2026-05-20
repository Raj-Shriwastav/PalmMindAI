from pypdf import PdfReader
import io


def extract_text_from_bytes(file_bytes: bytes, filename: str) -> str:
    """Extracts raw text content from PDF or TXT binary payloads with robust fallback decoders.

    Args:
        file_bytes: Inbound file binary data.
        filename: Full uploaded filename for extension detection.

    Returns:
        Cleaned, stripped plain text.
    """
    cleaned_filename = filename.lower().strip()

    if cleaned_filename.endswith(".pdf"):
        try:
            pdf_file = io.BytesIO(file_bytes)
            reader = PdfReader(pdf_file)
            text_parts = []

            for idx, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

            extracted_text = "\n".join(text_parts).strip()
            if not extracted_text:
                raise ValueError(
                    "The uploaded PDF file contains no extractable text or is image-only."
                )
            return extracted_text
        except Exception as e:
            raise RuntimeError(f"Failed to parse PDF document structures: {str(e)}")

    elif cleaned_filename.endswith(".txt"):
        try:
            # Default to UTF-8 decoding
            return file_bytes.decode("utf-8").strip()
        except UnicodeDecodeError:
            try:
                # Fallback to Latin-1
                return file_bytes.decode("latin-1").strip()
            except Exception as e:
                raise ValueError(f"Failed to decode TXT text stream: {str(e)}")

    else:
        raise ValueError(
            "Unsupported format. The ingestion pipeline accepts only PDF (.pdf) or Text (.txt) files."
        )
