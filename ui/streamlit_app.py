import streamlit as st
import tempfile
import os
import uuid
import time
from app.config import QDRANT_COLLECTION, RAG_CONTEXT_SIZE
from app.logger import logger
from app.services.extraction_service import extract_text_from_file, create_chunks
from app.services.llm_service import generate_embedding, get_rag_answer
from app.services.vector_service import qdrant_client, ensure_collection, upsert_points, search_vectors, delete_collection
from app.services.image_service import process_pdf_images_and_store
from qdrant_client.http.models import PointStruct

def main():
    st.set_page_config(page_title="Document Uploader & Semantic Search", layout="wide")
    st.title("📄 Document Uploader & Semantic Search")

    # --- Upload Section ---
    st.header("Upload Documents")

    process_images = st.checkbox("Process images from PDFs", value=True)

    uploaded_files = st.file_uploader(
        "Choose PDF files to upload",
        type=["pdf", "txt", "csv", "xlsx"],
        accept_multiple_files=True
    )

    if st.button("Clear Storage"):
        try:
            delete_collection()
            st.success(f"Collection has been deleted.")
            st.session_state.upload_complete = False
            st.session_state.uploaded_files_list = []
            st.rerun()
        except Exception as e:
            st.error(f"Failed to delete collection: {str(e)}")

    if 'upload_complete' not in st.session_state:
        st.session_state.upload_complete = False
    if 'uploaded_files_list' not in st.session_state:
        st.session_state.uploaded_files_list = []

    if uploaded_files and not st.session_state.upload_complete:
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
                            "source_type": "document"
                        }
                    ))
                if points:
                    upsert_points(points)

            # 3. Process images if PDF
            if process_images and file_ext.lower() == "pdf":
                try:
                    process_pdf_images_and_store(uploaded_file, tmp_path)
                except Exception as e:
                    logger.error(f"Failed to process images: {str(e)}")

            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                
            st.session_state.uploaded_files_list.append(uploaded_file.name)
            elapsed = time.time() - start_time
            total_processing_time += elapsed
            
        logger.info(f"Total processing time: {total_processing_time:.2f}s")
        progress_bar.empty()
        status_text.empty()
        st.success(f"✅ Successfully processed {len(uploaded_files)} file(s)")
        st.session_state.upload_complete = True

    elif st.session_state.uploaded_files_list:
        st.info(f"📁 Previously uploaded: {', '.join(st.session_state.uploaded_files_list)}")

    if st.session_state.upload_complete:
        if st.button("Upload New Files"):
            st.session_state.upload_complete = False
            st.session_state.uploaded_files_list = []
            st.rerun()

    # --- Search Section ---
    st.header("Search Box")
    query = st.text_input("Enter your search query:")

    if st.button("Search") and query:
        try:
            logger.info(f"Searching for: '{query}'")
            query_vector = generate_embedding(query)
            results = search_vectors(query_vector, limit=10)
            
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
