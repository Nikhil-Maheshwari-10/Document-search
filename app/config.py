import os
from dotenv import load_dotenv

load_dotenv()

# Embedding Configuration
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Text Processing Configuration
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP"))
RAG_CONTEXT_SIZE = int(os.getenv("RAG_CONTEXT_SIZE"))

# Qdrant Configuration
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION")

# Model Configuration
IMAGE_MODEL = os.getenv("IMAGE_MODEL")
RAG_MODEL = os.getenv("RAG_MODEL")

# Prompt Configuration
LLM_IMAGE_PROMPT = os.getenv("IMAGE_PROMPT")

RAG_SYSTEM_PROMPT = os.getenv("RAG_SYSTEM_PROMPT")

# App UI Configuration
UPLOAD_FOLDER = 'files'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'csv', 'xlsx'}
