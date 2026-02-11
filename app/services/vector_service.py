from qdrant_client import QdrantClient
import time
from datetime import datetime
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue, PayloadSchemaType
from app.config import QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION, EMBEDDING_DIM, STORAGE_TIMEOUT_MINUTES
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
            
            # Create payload indexes for efficient filtering
            qdrant_client.create_payload_index(
                collection_name=QDRANT_COLLECTION,
                field_name="session_id",
                field_schema=PayloadSchemaType.KEYWORD
            )
            qdrant_client.create_payload_index(
                collection_name=QDRANT_COLLECTION,
                field_name="source_type",
                field_schema=PayloadSchemaType.KEYWORD
            )
            logger.info("Created payload indexes for 'session_id' and 'source_type'")
        else:
            # Check for dimension mismatch
            collection_info = qdrant_client.get_collection(collection_name=QDRANT_COLLECTION)
            existing_size = collection_info.config.params.vectors.size
            if existing_size != EMBEDDING_DIM:
                logger.error(f"Dimension mismatch: '{QDRANT_COLLECTION}' has dimension {existing_size}, but config expects {EMBEDDING_DIM}.")
                raise ValueError(f"Qdrant Dimension Mismatch: {existing_size} vs {EMBEDDING_DIM}. Please 'Clear Storage' in the app to recreate the collection.")
            
            # Proactively ensure indexes exist on the existing collection
            try:
                qdrant_client.create_payload_index(
                    collection_name=QDRANT_COLLECTION,
                    field_name="session_id",
                    field_schema=PayloadSchemaType.KEYWORD
                )
                qdrant_client.create_payload_index(
                    collection_name=QDRANT_COLLECTION,
                    field_name="source_type",
                    field_schema=PayloadSchemaType.KEYWORD
                )
            except Exception as index_err:
                # Qdrant might throw if already exists, we can log and continue
                logger.debug(f"Index check/creation on existing collection: {index_err}")
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

def search_vectors(query_vector, session_id, limit=5):
    try:
        # Create a filter to only search within the specific session
        search_filter = Filter(
            must=[
                FieldCondition(
                    key="session_id",
                    match=MatchValue(value=session_id)
                )
            ]
        )
        
        search_result = qdrant_client.query_points(
            collection_name=QDRANT_COLLECTION,
            query=query_vector,
            query_filter=search_filter,
            limit=limit,
            with_payload=True
        )
        return search_result.points
    except Exception as e:
        logger.error(f"Error searching documents for session {session_id}: {e}")
        return []

def delete_session_data(session_id):
    """Deletes all points belonging to a specific session."""
    try:
        qdrant_client.delete(
            collection_name=QDRANT_COLLECTION,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="session_id",
                        match=MatchValue(value=session_id)
                    )
                ]
            )
        )
        logger.info(f"Deleted all points for session {session_id}")
    except Exception as e:
        logger.error(f"Failed to delete session data: {str(e)}")
        raise

def delete_collection():
    try:
        qdrant_client.delete_collection(collection_name=QDRANT_COLLECTION)
        logger.info(f"Deleted '{QDRANT_COLLECTION}'")
    except Exception as e:
        logger.error(f"Failed to delete collection: {str(e)}")
        raise

def update_last_activity(session_id):
    """Updates a marker in Qdrant with the current timestamp for a specific session."""
    try:
        # We use a zero-vector and the session_id (which is a UUID) for the activity marker
        marker_id = session_id
        timestamp = time.time()
        point = PointStruct(
            id=marker_id,
            vector=[0.0] * EMBEDDING_DIM,
            payload={
                "source_type": "activity_marker",
                "session_id": session_id,
                "last_activity": timestamp,
                "human_readable": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )
        qdrant_client.upsert(collection_name=QDRANT_COLLECTION, points=[point])
        logger.debug(f"Updated activity for session {session_id}: {timestamp}")
    except Exception as e:
        logger.warning(f"Failed to update activity marker for session {session_id}: {e}")

def check_auto_cleanup(session_id):
    """Checks if the session's data should be cleared due to inactivity."""
    try:
        marker_id = session_id
        collections = qdrant_client.get_collections().collections
        if not any(c.name == QDRANT_COLLECTION for c in collections):
            return

        result = qdrant_client.retrieve(
            collection_name=QDRANT_COLLECTION,
            ids=[marker_id],
            with_payload=True
        )

        if not result:
            return

        last_activity = result[0].payload.get("last_activity")
        if last_activity:
            elapsed_minutes = (time.time() - last_activity) / 60
            if elapsed_minutes > STORAGE_TIMEOUT_MINUTES:
                logger.info(f"Auto-cleanup triggered for session {session_id}: {elapsed_minutes:.1f}m inactivity")
                delete_session_data(session_id)
    except Exception as e:
        logger.error(f"Error during auto-cleanup check for session {session_id}: {e}")

def get_last_activity(session_id):
    """Retrieves the last activity timestamp for a session."""
    try:
        marker_id = session_id
        result = qdrant_client.retrieve(
            collection_name=QDRANT_COLLECTION,
            ids=[marker_id],
            with_payload=True
        )
        if result:
            return result[0].payload.get("last_activity")
    except Exception as e:
        logger.warning(f"Failed to get activity for session {session_id}: {e}")
    return None

def get_session_filenames(session_id):
    """Retrieves unique filenames uploaded for a given session."""
    try:
        result_points, _ = qdrant_client.scroll(
            collection_name=QDRANT_COLLECTION,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="session_id",
                        match=MatchValue(value=session_id)
                    ),
                    FieldCondition(
                        key="source_type",
                        match=MatchValue(value="document")
                    )
                ]
            ),
            limit=1000,
            with_payload=True,
            with_vectors=False
        )
        
        filenames = set()
        for point in result_points:
            fname = point.payload.get("filename")
            if fname:
                filenames.add(fname)
        
        return sorted(list(filenames))

    except Exception as e:
        logger.error(f"Failed to retrieve filenames for session {session_id}: {e}")
        return []

def perform_global_cleanup():
    """Scans for and deletes ALL expired sessions in the whole collection."""
    try:
        collections = qdrant_client.get_collections().collections
        if not any(c.name == QDRANT_COLLECTION for c in collections):
            return

        # Search for all activity markers
        markers = qdrant_client.scroll(
            collection_name=QDRANT_COLLECTION,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="source_type",
                        match=MatchValue(value="activity_marker")
                    )
                ]
            ),
            limit=100, # Clean up to 100 sessions at a time
            with_payload=True,
            with_vectors=False
        )[0]

        if not markers:
            return

        current_time = time.time()
        cleaned_count = 0

        for marker in markers:
            last_act = marker.payload.get("last_activity")
            sid = marker.payload.get("session_id")
            
            if last_act and sid:
                elapsed_min = (current_time - last_act) / 60
                if elapsed_min > STORAGE_TIMEOUT_MINUTES:
                    logger.info(f"Global Cleanup: Purging expired session {sid} ({elapsed_min:.1f}m inactive)")
                    delete_session_data(sid)
                    cleaned_count += 1
        
        if cleaned_count > 0:
            logger.info(f"Global Cleanup complete. Removed {cleaned_count} zombie sessions.")
    except Exception as e:
        logger.error(f"Failed to perform global cleanup: {e}")
