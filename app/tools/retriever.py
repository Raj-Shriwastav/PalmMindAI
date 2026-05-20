from langchain_core.tools import tool
from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.qdrant import client as qdrant_client
from app.repositories.document import DocumentRepository

# Initialize TextEmbedding once for tool execution
embedder = TextEmbedding(model_name=settings.EMBEDDING_MODEL_NAME)


@tool
def retrieve_knowledge(query: str) -> str:
    """Queries the Qdrant vector database to fetch relevant company documents, text files, or company rules.

    Use this tool whenever the user asks about PalmMind company culture, working hours, policies, role specifics,
    or technical configurations.

    Args:
        query: The semantic search query string.

    Returns:
        A formatted listing of relevant document context chunks.
    """
    try:
        # 1. Embed query
        embeddings = list(embedder.embed([query]))
        query_vector = embeddings[0].tolist()

        # 2. Query Qdrant
        hits = qdrant_client.search(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            query_vector=query_vector,
            limit=4,
        )

        if not hits:
            return "No matching document context was found in the vector database."

        # 3. Pull actual texts from Postgres (Postgres acts as single source of truth for metadata)
        db: Session = SessionLocal()
        try:
            repo = DocumentRepository(db)

            contexts = []
            for hit in hits:
                q_uuid = hit.id
                chunk_rec = repo.get_chunk_by_qdrant_uuid(q_uuid)

                if chunk_rec:
                    contexts.append(
                        f"--- Source: {chunk_rec.document.filename} (Score: {hit.score:.4f}) ---\n"
                        f"{chunk_rec.text_content.strip()}"
                    )
        finally:
            db.close()

        if not contexts:
            return "Retrieved vector matches but metadata resolved to empty database entries."

        return "\n\n".join(contexts)

    except Exception as e:
        return f"Error executing document knowledge retrieval: {str(e)}"
