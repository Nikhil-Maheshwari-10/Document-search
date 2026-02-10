from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from app.config import QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION, EMBEDDING_DIM
from app.logger import logger

def get_qdrant_client():
    return QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
    )

qdrant_client = get_qdrant_client()

def ensure_collection():
    try:
        collections = qdrant_client.get_collections().collections
        collection_names = [c.name for c in collections]
        if QDRANT_COLLECTION not in collection_names:
            qdrant_client.create_collection(
                collection_name=QDRANT_COLLECTION,
                vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE)
            )
            logger.info(f"Created '{QDRANT_COLLECTION}' with dimension {EMBEDDING_DIM}")
        else:
            # Check for dimension mismatch
            collection_info = qdrant_client.get_collection(collection_name=QDRANT_COLLECTION)
            existing_size = collection_info.config.params.vectors.size
            if existing_size != EMBEDDING_DIM:
                logger.error(f"Dimension mismatch: '{QDRANT_COLLECTION}' has dimension {existing_size}, but config expects {EMBEDDING_DIM}.")
                raise ValueError(f"Qdrant Dimension Mismatch: {existing_size} vs {EMBEDDING_DIM}. Please 'Clear Storage' in the app to recreate the collection.")
    except Exception as e:
        logger.error(f"Failed to check or create Qdrant collection: {str(e)}")
        raise

def upsert_points(points):
    try:
        qdrant_client.upsert(collection_name=QDRANT_COLLECTION, points=points)
        logger.info(f"Stored {len(points)} points in Qdrant")
    except Exception as e:
        logger.error(f"Failed to upsert points: {str(e)}")
        raise

def search_vectors(query_vector, limit=5):
    try:
        search_result = qdrant_client.search(
            collection_name=QDRANT_COLLECTION,
            query_vector=query_vector,
            limit=limit,
            with_payload=True
        )
        return search_result
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        return []

def delete_collection():
    try:
        qdrant_client.delete_collection(collection_name=QDRANT_COLLECTION)
        logger.info(f"Deleted '{QDRANT_COLLECTION}'")
    except Exception as e:
        logger.error(f"Failed to delete collection: {str(e)}")
        raise
