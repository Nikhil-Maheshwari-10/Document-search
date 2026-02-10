from litellm import embedding, completion
from app.config import EMBEDDING_MODEL, GEMINI_API_KEY, EMBEDDING_DIM, RAG_MODEL, RAG_SYSTEM_PROMPT
from app.logger import logger

def generate_embedding(text):
    """Generate embedding vector for given text"""
    try:
        response = embedding(
            input=[text],
            model=EMBEDDING_MODEL,
            api_key=GEMINI_API_KEY,
        )
        return response['data'][0]['embedding']
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return [0.0] * EMBEDDING_DIM

def get_rag_answer(query, context_text):
    """Generate RAG answer using LLM"""
    if not context_text.strip():
        return "Not found in the provided documents"
        
    prompt = (
        f"{RAG_SYSTEM_PROMPT}\n\n"
        + f"Context:\n{context_text}\n\nUser Query: {query}\n\nAnswer:"
    )
    
    try:
        llm_response = completion(
            model=RAG_MODEL,
            api_key=GEMINI_API_KEY,
            temperature=0.1,
            messages=[
                {"role": "user", "content": [{"type": "text", "text": prompt}]}
            ]
        )
        answer = llm_response['choices'][0]['message']['content']
        usage = llm_response.get("usage", {})
        logger.info(f"[RAG LLM] Input tokens: {usage.get('prompt_tokens', 'N/A')}, Output tokens: {usage.get('completion_tokens', 'N/A')}")
        return answer
    except Exception as e:
        logger.error(f"LLM RAG answer failed: {str(e)}")
        return f"Error generating answer: {str(e)}"
