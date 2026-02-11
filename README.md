# Document Uploader & Semantic Search

Welcome to the **Document Uploader & Semantic Search** app! This project provides a user-friendly interface for uploading documents (PDF files only), extracting their content, and performing powerful semantic search using vector embeddings and Qdrant.

## Features

- 📄 **Upload Documents:**
  - Supports PDF, TXT, CSV, and XLSX files.
  - Extracts text and (optionally) processes images from PDFs.
- 🔍 **Semantic Search:**
  - Search across all uploaded documents using natural language queries.
  - Retrieves the most relevant text and image descriptions using vector search.
- 🧠 **RAG (Retrieval-Augmented Generation):**
  - Uses high-performance Gemini models to generate answers based on retrieved context.
- 🖼️ **Image Understanding:**
  - Extracts and describes images/charts/graphs from PDFs using AI.
- ⚡ **Optimization:**
  - **Smart Caching**: Database initialization and indexes are cached to ensure instantaneous UI responsiveness.
  - **Throttled Tasks**: Background cleanups and status checks are throttled to avoid redundant cloud requests.
  - **Configurable RAG**: Adjustable context size and model selection for balancing accuracy and latency.
- 🛡️ **Storage Management & Multi-Tenancy:**
  - **Isolated Sessions**: Every user has a private session. You only see your own documents and search results.
  - **Auto-Cleanup**: Your session data is automatically cleared after 60 minutes of inactivity.
  - **Hibernation Sync**: A global sweep purges "zombie" data from past sessions whenever the app wakes from hibernation.
  - **Targeted Clear**: The "Clear Storage" button wipes *only* your data, leaving other users' data safe.
  - **Storage Status**: Sidebar timer showing exactly when *your* specific session will be cleared.

## How It Works

1. **Upload** your documents via the web interface. 
2. The app extracts text (and optionally image content) and generates vector embeddings tagged with your unique **Session ID**.
3. All embeddings are stored in a shared Qdrant collection, isolated by your session ID for privacy.
4. Enter a search query to find relevant context **only from your own files**.
5. The top relevant context (both text and images) is passed to the LLM to generate a final answer.

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Nikhil-Maheshwari-10/Document-search.git
   cd Document-search
   ```
2. **Install dependencies using Poetry:**
   ```bash
   poetry install
   ```
3. **Set up environment variables:**
   - Create a `.env` file with the following keys:
     ```env
     GEMINI_API_KEY=your_gemini_api_key
     EMBEDDING_MODEL="gemini/gemini-embedding-001"
     QDRANT_URL=your_qdrant_url
     QDRANT_API_KEY=your_qdrant_api_key
     EMBEDDING_DIM=3072
     QDRANT_COLLECTION="Your Collection Name"
     RAG_CONTEXT_SIZE=5
     STORAGE_TIMEOUT_MINUTES=60

     IMAGE_MODEL="gemini/gemini-2.5-flash"
     RAG_MODEL="gemini/gemini-2.5-flash-lite"

     IMAGE_PROMPT="Your image prompt here..."
     RAG_SYSTEM_PROMPT="Your RAG system prompt here..."
     ```
4. **Run the app:**
   ```bash
   poetry run python main.py
   ```

## Usage

- **Upload Section:**
  - Select and upload your documents (multi-file support).
  - Optionally enable/disable image processing for PDFs.
- **Search Section:**
  - Enter your query and click "Search".
  - View the generated answer and explore the "Show context" expander to see the specific snippets used by the AI.
- **Storage Status (Sidebar):**
  - View "Last Activity" time and the countdown until *your* data is automatically cleared. 
  - Note: Your timer resets every time you search or upload!
- **Clear Storage:**
  - Use the "Clear Storage" button to immediately delete points from your current session and force-reset the uploader.

## Deployment (Streamlit Cloud)

To deploy this app on Streamlit Cloud:

1. **Push your code to GitHub.**
2. **Connect to Streamlit Cloud**: Go to [share.streamlit.io](https://share.streamlit.io/) and connect your repository.
3. **Set the Main File Path**: Set it to `main.py`.
4. **Configure Secrets**:
   - Go to **Settings > Secrets** in the Streamlit Cloud dashboard.
   - Add your environment variables in TOML format (use triple quotes for prompts):
     ```toml
     GEMINI_API_KEY = "your_key..."
     EMBEDDING_MODEL = "gemini/gemini-embedding-001"
     QDRANT_URL = "your_url..."
     QDRANT_API_KEY = "your_key..."
     EMBEDDING_DIM = 3072
     QDRANT_COLLECTION = "Your Collection Name"
     RAG_CONTEXT_SIZE = 5
     STORAGE_TIMEOUT_MINUTES = 60

     IMAGE_MODEL = "gemini/gemini-2.5-flash"
     RAG_MODEL = "gemini/gemini-2.5-flash-lite"

     IMAGE_PROMPT = """Your multi-line prompt here..."""
     RAG_SYSTEM_PROMPT = """Your multi-line system prompt here..."""
     ```
5. **Python Version**: Ensure you select **Python 3.12** or **3.13** in the Streamlit Cloud advanced settings (avoid 3.14 unless you are sure pre-built wheels are available).

## License

This project is licensed under the MIT License.

---

**Enjoy fast, accurate, and user-friendly document search!**
