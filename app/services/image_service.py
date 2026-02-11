import os
import io
import fitz
import base64
import uuid
import time
import tempfile
from PIL import Image
from litellm import completion
from qdrant_client.http.models import PointStruct
from app.config import GEMINI_API_KEY, LLM_IMAGE_PROMPT, QDRANT_COLLECTION, IMAGE_MODEL
from app.logger import logger
from app.services.llm_service import generate_embedding
from app.services.vector_service import qdrant_client

def process_pdf_images_and_store(uploaded_file, tmp_path, session_id):
    """Process images in a PDF, generate descriptions, and store in Qdrant"""
    doc = fitz.open(tmp_path)
    logger.info(f"Processing PDF '{uploaded_file.name}' with {len(doc)} pages (Session: {session_id})")
    
    total_images_found = 0
    pages_with_large_images = 0

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        image_list = page.get_images(full=True)
        total_images_found += len(image_list)
        
        has_large_image = False
        reason = "no images found"
        if image_list:
            reason = "all images too small (<300x120)"
            for img in image_list:
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                if pix.width > 300 and pix.height > 120:
                    has_large_image = True
                    break
        
        if has_large_image:
            pages_with_large_images += 1
            logger.info(f"Page {page_num+1}: Large image(s) detected. Generating description...")
            
            # Render the whole page as an image
            page_pix = page.get_pixmap(dpi=450)
            img_pil = Image.open(io.BytesIO(page_pix.tobytes("png")))
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as img_temp:
                img_pil.save(img_temp.name, "PNG", optimize=True)
                img_temp_path = img_temp.name
                
            with open(img_temp_path, "rb") as img_file:
                img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
            
            max_retries = 3
            retry_count = 0
            description = None
            while retry_count < max_retries and description is None:
                try:
                    time.sleep(4)  # Small delay to avoid rate limiting
                    llm_response = completion(
                        model=IMAGE_MODEL,
                        api_key=GEMINI_API_KEY,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": LLM_IMAGE_PROMPT},
                                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}}
                                ]
                            }
                        ]
                    )
                    description = llm_response['choices'][0]['message']['content']
                    usage = llm_response.get("usage", {})
                    logger.info(f"[IMAGE LLM] Page {page_num+1}: Input tokens: {usage.get('prompt_tokens', 'N/A')}, Output tokens: {usage.get('completion_tokens', 'N/A')}")
                except Exception as e:
                    retry_count += 1
                    logger.warning(f"Page {page_num+1}: LLM description attempt {retry_count} failed: {str(e)}")
                    time.sleep(2 ** retry_count)
            
            if description and description.strip().lower() != "none":
                image_dimensions = f"{img_pil.width}x{img_pil.height}"
                chunk = description.strip()
                
                if len(chunk) >= 20:
                    chunk_embedding = generate_embedding(chunk)
                    unique_id = str(uuid.uuid4())
                    
                    point = PointStruct(
                        id=unique_id,
                        vector=chunk_embedding,
                        payload={
                            "filename": f"{uploaded_file.name}_page_{page_num+1}_fullpage",
                            "document": chunk,
                            "source_type": "image_description",
                            "session_id": session_id,
                            "page": page_num+1,
                            "dimensions": image_dimensions
                        }
                    )
                    
                    try:
                        qdrant_client.upsert(collection_name=QDRANT_COLLECTION, points=[point])
                        logger.info(f"Page {page_num+1}: Successfully stored image description in Qdrant")
                    except Exception as upsert_ex:
                        logger.error(f"Page {page_num+1}: Failed to store image embedding: {str(upsert_ex)}")
            elif description and description.strip().lower() == "none":
                logger.info(f"Page {page_num+1}: AI determined image is not relevant (returned 'none')")
            
            if os.path.exists(img_temp_path):
                os.remove(img_temp_path)
        else:
            logger.debug(f"Page {page_num+1}: Skipped ({reason})")
                
    if total_images_found == 0:
        logger.info(f"No images found in PDF '{uploaded_file.name}'")
    else:
        logger.info(f"Image processing complete for '{uploaded_file.name}'. Found {total_images_found} images total across {len(doc)} pages. Processed {pages_with_large_images} pages with significant images.")
    
    doc.close()
