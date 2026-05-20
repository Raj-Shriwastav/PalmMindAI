from qdrant_client import QdrantClient
from qdrant_client.http import models as qd_models
from app.core.config import settings

# Initialize Qdrant Client targeting configured endpoint
client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)


def init_qdrant_collection() -> None:
    """Verify and initialize target vector collection on startup."""
    collection_name = settings.QDRANT_COLLECTION_NAME
    try:
        collections = client.get_collections()
        exists = any(c.name == collection_name for c in collections.collections)

        if not exists:
            # Snowflake/snowflake-arctic-embed-m outputs dense vector embeddings of 768 dimensions.
            # We map this to Cosine distance for high-fidelity text retrieval comparisons.
            client.create_collection(
                collection_name=collection_name,
                vectors_config=qd_models.VectorParams(
                    size=768, distance=qd_models.Distance.COSINE
                ),
            )
            print(
                f"[QDRANT] Created new collection '{collection_name}' (768 dimensions, Cosine)."
            )
        else:
            print(f"[QDRANT] Collection '{collection_name}' is already active.")
    except Exception as e:
        print(f"[QDRANT ERROR] Failed to initialize collection: {str(e)}")


def get_qdrant_client() -> QdrantClient:
    """FastAPI Dependency yielding the singleton QdrantClient instance."""
    return client
