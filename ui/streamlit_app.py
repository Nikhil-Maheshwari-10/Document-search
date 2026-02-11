import streamlit as st
import tempfile
import os
import uuid
import time
from datetime import datetime
from app.config import QDRANT_COLLECTION, RAG_CONTEXT_SIZE, STORAGE_TIMEOUT_MINUTES
from app.logger import logger
from app.services.extraction_service import extract_text_from_file, create_chunks
from app.services.llm_service import generate_embedding, get_rag_answer
from app.services.vector_service import qdrant_client, ensure_collection, upsert_points, search_vectors, delete_session_data, check_auto_cleanup, update_last_activity, get_last_activity, perform_global_cleanup, get_session_filenames
from app.services.image_service import process_pdf_images_and_store
from qdrant_client.http.models import PointStruct

# --- Latency Optimizations ---

@st.cache_resource(show_spinner="Initializing Database...")
def init_qdrant():
    """Ensures collection and indexes exist once per app process."""
    ensure_collection()
    return True

def run_throttled_cleanup(session_id):
    """Runs cleanups only when necessary to avoid blocking UI actions."""
    # Global cleanup: Run once per browser session start
    if 'global_cleanup_done' not in st.session_state:
        perform_global_cleanup()
        st.session_state.global_cleanup_done = True
    
    # Session cleanup: Run only if we haven't checked recently (every 5 mins)
    now = time.time()
    if 'last_cleanup_check' not in st.session_state or (now - st.session_state.last_cleanup_check > 300):
        check_auto_cleanup(session_id)
        st.session_state.last_cleanup_check = now

@st.cache_data(ttl=60) # Cache for 1 minute to avoid spamming Qdrant on every click
def cached_get_last_activity(session_id):
    return get_last_activity(session_id)

def main():
    st.set_page_config(page_title="Document Uploader & Semantic Search", layout="wide", initial_sidebar_state="collapsed")
    st.title("📄 Document Uploader & Semantic Search")
    
    # Initialize session state for UI sync and Multi-tenancy
    # Use query parameters to persist session across refreshes
    query_params = st.query_params
    
    if 'session_id' not in st.session_state:
        # Check if session_id exists in URL query params
        if 'sid' in query_params:
            st.session_state.session_id = query_params['sid']
            logger.info(f"Restored session from URL: {st.session_state.session_id}")
        else:
            # Create new session and add to URL
            st.session_state.session_id = str(uuid.uuid4())
            st.query_params['sid'] = st.session_state.session_id
            logger.info(f"Created new session: {st.session_state.session_id}")
    
    if 'uploader_key' not in st.session_state:
        st.session_state.uploader_key = 0
    if 'clear_context_msg' not in st.session_state:
        st.session_state.clear_context_msg = False
    if 'upload_complete' not in st.session_state:
        st.session_state.upload_complete = False
    if 'uploaded_files_list' not in st.session_state:
        st.session_state.uploaded_files_list = []
    
    session_id = st.session_state.session_id
    
    # Restore uploaded files list from Qdrant if session has data but UI doesn't know about it
    if not st.session_state.uploaded_files_list:
        stored_filenames = get_session_filenames(session_id)
        if stored_filenames:
            st.session_state.uploaded_files_list = stored_filenames
            logger.info(f"Restored {len(stored_filenames)} files from Qdrant for session {session_id}")

    # 1. Initialize DB (Cached)
    init_qdrant()

    # 2. Throttled Cleanups (Avoid blocking UI reruns)
    run_throttled_cleanup(session_id)

    # --- Sidebar: Storage Status ---
    with st.sidebar:
        st.header("⚙️ Storage Status")
        last_act = cached_get_last_activity(session_id)
        if last_act:
            st.write(f"**Last Activity:** {datetime.fromtimestamp(last_act).strftime('%Y-%m-%d %H:%M:%S')}")
            elapsed_min = (time.time() - last_act) / 60
            remaining = max(0, STORAGE_TIMEOUT_MINUTES - elapsed_min)
            
            if remaining > 0:
                st.info(f"⏳ Auto-clear in: **{int(remaining)} mins**")
            else:
                st.warning("⚠️ Storage is pending cleanup on refresh.")
        else:
            st.info("No active session data found.")
        
        st.divider()
        st.caption(f"Session isolation is active.")
        st.caption(f"Auto-cleanup is set to {STORAGE_TIMEOUT_MINUTES} minutes of inactivity.")

    # Success message persistent across rerun
    if st.session_state.clear_context_msg:
        st.success("✅ Storage has been cleared.")
        st.session_state.clear_context_msg = False

    # --- Upload Section ---
    st.header("Upload Documents")

    process_images = st.checkbox("Process images from PDFs", value=True)

    uploaded_files = st.file_uploader(
        "Choose PDF files to upload",
        type=["pdf", "txt", "csv", "xlsx"],
        accept_multiple_files=True,
        key=f"uploader_{st.session_state.uploader_key}"
    )

    # Previously Uploaded Files Info
    if st.session_state.uploaded_files_list:
        st.info(f"📁 Previously uploaded: {', '.join(st.session_state.uploaded_files_list)}")

    # Action Buttons Layout
    # Use consistent proportions that work well with sidebar open/closed
    col_process, col_clear, _ = st.columns([8, 9, 83], gap="small")
    
    start_processing = False
    with col_process:
        if st.button("Process Files"):
            start_processing = True

    with col_clear:
        # Only show Clear Storage if we have data
        if st.session_state.uploaded_files_list:
             if st.button("Clear Storage"):
                try:
                    delete_session_data(session_id)
                    cached_get_last_activity.clear() # Reset UI status
                    ensure_collection() # Ensure it's ready for next use
                    st.session_state.uploader_key += 1 # Reset uploader
                    st.session_state.upload_complete = False
                    st.session_state.uploaded_files_list = []
                    st.session_state.clear_context_msg = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to delete collection: {str(e)}")

    # Processing Logic
    if start_processing:
        if not uploaded_files:
            st.warning("Please select files to upload first.")
        else:
            try:
                ensure_collection()
            except Exception as e:
                st.error(f"Failed to setup collection: {str(e)}")
                st.stop()
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            total_processing_time = 0
            for idx, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"Processing {uploaded_file.name}...")
                progress_bar.progress((idx + 1) / len(uploaded_files))
                
                start_time = time.time()

                file_ext = uploaded_file.name.split('.')[-1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    tmp_path = tmp_file.name

                logger.info(f"Processing file: {uploaded_file.name}")

                # 1. Extract text
                text = extract_text_from_file(tmp_path)
                
                # 2. Vectorize and store text
                if text:
                    chunks = create_chunks(text)
                    points = []
                    for chunk in chunks:
                        chunk_embedding = generate_embedding(chunk)
                        u_id = str(uuid.uuid4())
                        points.append(PointStruct(
                            id=u_id,
                            vector=chunk_embedding,
                            payload={
                                "filename": uploaded_file.name,
                                "document": chunk,
                                "source_type": "document",
                                "session_id": session_id
                            }
                        ))
                    if points:
                        upsert_points(points)

                # 3. Process images if PDF
                if process_images and file_ext.lower() == "pdf":
                    try:
                        process_pdf_images_and_store(uploaded_file, tmp_path, session_id)
                    except Exception as e:
                        logger.error(f"Failed to process images: {str(e)}")

                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                    
                st.session_state.uploaded_files_list.append(uploaded_file.name)
                elapsed = time.time() - start_time
                total_processing_time += elapsed
                
            logger.info(f"Total processing time: {total_processing_time:.2f}s")
            update_last_activity(session_id) # Store the timestamp
            cached_get_last_activity.clear() # Force sidebar to fetch new data
            progress_bar.empty()
            status_text.empty()
            st.success(f"✅ Successfully processed {len(uploaded_files)} file(s)")
            
            # Reset uploader for next batch
            st.session_state.uploader_key += 1
            st.rerun()

    # --- Search Section ---
    st.header("Search Box")
    query = st.text_input("Enter your search query:")

    if st.button("Search") and query:
        try:
            logger.info(f"Searching for session {session_id}: '{query}'")
            update_last_activity(session_id) # Prolong storage life on search
            cached_get_last_activity.clear() # Force sidebar refresh
            query_vector = generate_embedding(query)
            results = search_vectors(query_vector, session_id, limit=10)
            
            if results:
                doc_results = [res for res in results if res.payload.get("source_type") == "document"]
                img_results = [res for res in results if res.payload.get("source_type") == "image_description"]
                
                # RAG
                if results:
                    # Combine document snippets and image descriptions for context
                    context_text = "\n\n".join([
                        f"[{res.payload.get('source_type', 'unknown')}] {res.payload.get('document', '')}" 
                        for res in results[:RAG_CONTEXT_SIZE]
                    ])
                    answer = get_rag_answer(query, context_text)
                    st.subheader("RAG Answer")
                    st.write(answer)
                
                # Details Display
                with st.expander("Show context"):
                    for i, res in enumerate(results[:RAG_CONTEXT_SIZE], 1):
                        source = res.payload.get('source_type', 'unknown')
                        st.markdown(f"**[{source.upper()}] Chunk {i} from {res.payload.get('filename')}**")
                        st.write(res.payload.get("document", ""))
                        st.divider()
            else:
                st.info("No results found.")
        except Exception as e:
            st.error(f"Search failed: {str(e)}")

if __name__ == "__main__":
    main()