import re
from typing import List
import numpy as np
from fastembed import TextEmbedding
from app.core.config import settings


class RecursiveCharacterChunker:
    """Recursively splits text using hierarchical separators to maintain semantic structure."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = ["\n\n", "\n", " ", ""]

    def chunk_text(self, text: str) -> List[str]:
        """Split text recursively into chunks based on separator list."""
        if not text:
            return []

        return self._split(text, self.separators)

    def _split(self, text: str, separators: List[str]) -> List[str]:
        """Hierarchically split and merge text to conform to target size and overlaps."""
        if len(text) <= self.chunk_size:
            return [text]

        if not separators:
            # If no separators left, hard split by character limit
            return [
                text[i : i + self.chunk_size]
                for i in range(0, len(text), self.chunk_size - self.chunk_overlap)
            ]

        separator = separators[0]
        next_separators = separators[1:]

        # Split text by the current active separator
        if separator == "":
            splits = list(text)
        else:
            splits = text.split(separator)

        chunks = []
        current_chunk = []
        current_length = 0

        for split in splits:
            # Re-insert the separator if it was omitted during split
            part = split + (separator if separator != "" else "")
            part_len = len(part)

            if part_len > self.chunk_size:
                # If a single part exceeds chunk size, split it with sub-separators first
                if current_chunk:
                    chunks.append("".join(current_chunk).strip())
                    current_chunk = []
                    current_length = 0

                sub_chunks = self._split(split, next_separators)
                chunks.extend(sub_chunks)
            elif current_length + part_len <= self.chunk_size:
                current_chunk.append(part)
                current_length += part_len
            else:
                # Store completed chunk
                if current_chunk:
                    chunks.append("".join(current_chunk).strip())

                # Rollback overlap characters to start the new chunk
                rollback_chunk = []
                rollback_len = 0
                for item in reversed(current_chunk):
                    if rollback_len + len(item) <= self.chunk_overlap:
                        rollback_chunk.insert(0, item)
                        rollback_len += len(item)
                    else:
                        break

                current_chunk = rollback_chunk + [part]
                current_length = rollback_len + part_len

        if current_chunk:
            chunks.append("".join(current_chunk).strip())

        return [c for c in chunks if c]


class SemanticChunker:
    """Uses FastEmbed embeddings and cosine distances to split text on semantic transition points."""

    def __init__(self, model_name: str = None, similarity_percentile: float = 90.0):
        # Default to configured Arctic model
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self.similarity_percentile = similarity_percentile
        # Initialize text embedder
        self.embedder = TextEmbedding(model_name=self.model_name)

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences using standard regex boundary markers."""
        sentences = re.split(r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|!)\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    def _cosine_distance(self, u: np.ndarray, v: np.ndarray) -> float:
        """Calculate cosine distance (1 - cosine similarity) between vectors."""
        dot_product = np.dot(u, v)
        norm_u = np.linalg.norm(u)
        norm_v = np.linalg.norm(v)

        if norm_u == 0 or norm_v == 0:
            return 1.0  # Maximum distance

        similarity = dot_product / (norm_u * norm_v)
        return float(1.0 - similarity)

    def chunk_text(self, text: str) -> List[str]:
        """Group sentences semantically by thresholding embedding cosine changes."""
        if not text:
            return []

        sentences = self._split_sentences(text)
        if len(sentences) <= 1:
            return sentences

        # Generate embeddings for each individual sentence
        embeddings = list(self.embedder.embed(sentences))

        # Calculate cosine distances between all consecutive sentence pairs
        distances = []
        for i in range(len(sentences) - 1):
            dist = self._cosine_distance(embeddings[i], embeddings[i + 1])
            distances.append(dist)

        # Calculate dynamic threshold based on distance percentile
        threshold = np.percentile(distances, self.similarity_percentile)

        chunks = []
        current_chunk_sentences = [sentences[0]]

        for i, dist in enumerate(distances):
            sentence = sentences[i + 1]
            if dist > threshold:
                # Transition detected: push active chunk and reset
                chunks.append(" ".join(current_chunk_sentences).strip())
                current_chunk_sentences = [sentence]
            else:
                current_chunk_sentences.append(sentence)

        if current_chunk_sentences:
            chunks.append(" ".join(current_chunk_sentences).strip())

        return [c for c in chunks if c]
