# Document Uploader & Semantic Search

Welcome to the **Document Uploader & Semantic Search** app! This project provides a user-friendly interface for uploading documents (PDF files only), extracting their content, and performing powerful semantic search using vector embeddings and Qdrant.

## Features

- 📄 **Upload Documents:**
  - Supports PDF files only.
  - Extracts text and (optionally) processes images from PDFs.
- 🔍 **Semantic Search:**
  - Search across all uploaded documents using natural language queries.
  - Retrieves the most relevant text and image descriptions using vector search.
- 🧠 **RAG (Retrieval-Augmented Generation):**
  - Uses LLMs to generate answers based on retrieved document context.
- 🖼️ **Image Understanding:**
  - Optionally extracts and describes images from PDFs using an LLM.
- ⚡ **Fast & Scalable:**
  - Uses Qdrant for efficient vector storage and retrieval.
- 🛡️ **Clear Storage:**
  - Easily clear all uploaded data and start fresh.

## How It Works

1. **Upload** your documents via the web interface.
2. The app extracts text (and optionally image content) and generates vector embeddings.
3. All embeddings are stored in a Qdrant collection for fast similarity search.
4. Enter a search query to find the most relevant document chunks and image descriptions.
5. The app uses an LLM to generate a detailed answer based on the retrieved context.

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
     EMBEDDING_DIM=768
     QDRANT_COLLECTION="My Collection"
     ```
4. **Run the app:**
   ```bash
   poetry run python main.py
   ```

## Usage

- **Upload Section:**
  - Select and upload your documents.
  - Optionally enable/disable image processing for PDFs.
- **Search Section:**
  - Enter your query and click "Search".
  - View the generated answer and the context used.
  - Expand to see relevant document chunks and image descriptions.
- **Clear Storage:**
  - Use the "Clear Storage" button to delete all uploaded data.

## Requirements

- Python 3.8+
- [Streamlit](https://streamlit.io/)
- [Qdrant](https://qdrant.tech/)
- [LangChain](https://python.langchain.com/)
- [PyPDF2](https://pypi.org/project/PyPDF2/), [Pillow](https://pillow.readthedocs.io/), [openpyxl](https://openpyxl.readthedocs.io/)
- [litellm](https://github.com/BerriAI/litellm)

## Notes

- Make sure your Qdrant instance is running and accessible.
- The app uses environment variables for API keys and configuration.
- For image understanding, a compatible LLM (e.g., Gemini) is required.

## Deployment (Streamlit Cloud)

To deploy this app on Streamlit Cloud:

1. **Push your code to GitHub.**
2. **Connect to Streamlit Cloud**: Go to [share.streamlit.io](https://share.streamlit.io/) and connect your repository.
3. **Set the Main File Path**: Set it to `main.py`.
4. **Configure Secrets**:
   - Streamlit Cloud does not use `.env` files. Instead, go to **Settings > Secrets** in the Streamlit Cloud dashboard.
   - Add your environment variables in TOML format:
     ```toml
     GEMINI_API_KEY = "your_key..."
     EMBEDDING_MODEL = "gemini/gemini-embedding-001"
     QDRANT_URL = "your_url..."
     QDRANT_API_KEY = "your_key..."
     EMBEDDING_DIM = 768
     QDRANT_COLLECTION = "My Collection"
     ```
5. **Python Version**: Ensure you select **Python 3.12** or **3.13** in the Streamlit Cloud advanced settings (avoid 3.14 unless you are sure pre-built wheels are available).

## License

This project is licensed under the MIT License.

---

**Enjoy fast, accurate, and user-friendly document search!**
