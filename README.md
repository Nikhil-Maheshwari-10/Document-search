# 📄 Document Uploader & Semantic Search

Welcome! This application provides a high-performance, user-friendly interface for uploading documents, extracting their content, and performing powerful **Semantic Search** and **RAG** (Retrieval-Augmented Generation). 🚀

---

## ✨ Features at a Glance

- **Multi-Format Extraction**: Seamlessly process PDF, TXT, CSV, and XLSX files.
- **AI-Powered Vision**: Optionally describe and analyze images, charts, and graphs within PDFs.
- **Smart RAG**: Get direct answers to your questions based on retrieved document context.
- **Private Sessions**: Multi-tenant isolation ensures your data stays private and secure.
- **Optimized Performance**: Near-instant responsiveness thanks to smart caching and throttled background tasks.

---

## 🏗️ Architecture: RAG Pipeline

![RAG Pipeline Flowchart](https://mermaid.ink/img/pako:eNp9VNtq4zAQ_RXhvioLS95c6FLitARaSJO2sGhDUa1xLCLLRpLblCT_vrr4os2G-kUjzZmjmTkjH5K8ZpCkyVbRpkTP2R-J7Kfb93CwkFvQhtcSkdFc8gYEl7AJYPe9NKKmjLxoUJ2t0R0XoDdoMrlB871RNDe1Ip3laNazPngeswwwH7RuBDcGFJmVrdxxuY2QvS-wV-_AnmFvyMPD4yXa3h9oLT88MUWlIa_gb3NHdPt_PWjywwYss7tZCfnusCic_es0wnqXIz7-Bn1Ei8oSdXUQv7mQUAzyOb1ybTtisyfBQtaM8IN7LDcDnX9XrvOflxsgINmZyCswisMHFYiM5gWRn1pQX0HjubTN1-FkM2YVEN-k5QGhZN_6NVCVl4MOfhcXHoF81Ky2F1uhuxUtFTQRvj920NXt_dtS1VVjSFicVxvV-umLgkbgEOeUcFXcgwRFL-B7LVagW2E0ybhuBP1Ct1J_gtqcdTrSwI_U0T4N27_jP_UFaC6o1hkUSIcGooILkV4VRYFt7vUO0qvpdNrZk0_OTJn-bPbXUfT4jHD_TPDwBHCUC47nEA9DhocBwqNmOE4V9y3okrxOcFKBqihnSXpITAmV-6cwKKjtTnLCSdswamDOuOVIUisCnP4CNg56LA==)

<details>
<summary>View Mermaid Source</summary>

```mermaid
graph TD
    %% Ingestion Pipeline
    subgraph Ingestion [Ingestion Pipeline]
        style Ingestion fill:#f5faff,stroke:#0055b3,stroke-width:2px
        Upload[User Uploads Files<br/><i>PDF, TXT, CSV, XLSX</i>] --> Extractor[<b>Extraction Service</b><br/>Extract raw text from file]
        Extractor --> Splitter[<b>Chunking</b><br/>RecursiveCharacterTextSplitter<br/><i>Size: 1000, Overlap: 100</i>]
        Splitter --> EmbedText[<b>LLM Service</b><br/>Generate Embeddings<br/><i>gemini-embedding-001</i>]
        EmbedText --> StoreQdrant[<b>Vector Storage</b><br/>Upsert into Qdrant Cloud<br/><i>Payload: filename, text, source_type</i>]

        %% Image processing branch
        Upload -.-> PDFCheck{If PDF &<br/>Process Images?}
        PDFCheck -->|Yes| ImageExtract[<b>Image Service</b><br/>Render pages with large images]
        ImageExtract --> VisionLLM[<b>Vision LLM</b><br/>Describe visuals/charts<br/><i>gemini-2.5-flash</i>]
        VisionLLM --> EmbedDesc[<b>LLM Service</b><br/>Embed Image Descriptions]
        EmbedDesc --> StoreQdrant
    end

    %% Retrieval Pipeline
    subgraph Retrieval [Retrieval Pipeline]
        style Retrieval fill:#fff9f5,stroke:#b35900,stroke-width:2px
        Query[User Enters Search Query] --> EmbedQuery[<b>LLM Service</b><br/>Generate Query Embedding]
        EmbedQuery --> VectorSearch[<b>Vector Search</b><br/>Query Qdrant for Session ID]
        VectorSearch --> Context[<b>Context Prep</b><br/>Combine top 5 text/image matches]
        Context --> RAG_Prompt[<b>Prompt Construction</b><br/>Inject context + System Prompt]
        RAG_Prompt --> RAG_LLM[<b>LLM Generation</b><br/>Generate final answer<br/><i>gemini-2.5-flash-lite</i>]
        RAG_LLM --> Results[Display Answer & Source Context]
    end

    %% Connection
    StoreQdrant -.->|Session Isolated Search| VectorSearch

    %% Styling
    classDef service fill:#fff,stroke:#333,stroke-width:1px;
    class Extractor,Splitter,EmbedText,StoreQdrant,ImageExtract,VisionLLM,EmbedDesc,EmbedQuery,VectorSearch,RAG_LLM service;
```
</details>

---

## 🛠️ Setup Instructions

Follow these steps to get the app running on your local machine:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Nikhil-Maheshwari-10/Document-search.git
   cd Document-search
   ```

2. **Install dependencies using Poetry:**
   ```bash
   # Ensure you have Poetry installed first!
   poetry install
   ```

3. **Set up environment variables:**
   Create a `.env` file in the root directory with the following keys:
   ```env
   GEMINI_API_KEY=your_gemini_api_key
   EMBEDDING_MODEL="your_model_name"

   QDRANT_URL=your_qdrant_url
   QDRANT_API_KEY=your_qdrant_api_key

   EMBEDDING_DIM=your_embedding_dimension
   CHUNK_SIZE=your_chunk_size
   CHUNK_OVERLAP=your_chunk_overlap
   QDRANT_COLLECTION="your_collection_name"
   RAG_CONTEXT_SIZE=your_rag_context_size
   STORAGE_TIMEOUT_MINUTES=your_storage_timeout_minutes

   IMAGE_MODEL="your_model_name"
   RAG_MODEL="your_model_name"

   IMAGE_PROMPT="Your image prompt here..."
   RAG_SYSTEM_PROMPT="Your RAG system prompt here..."
   ```

4. **Run the app:**
   ```bash
   poetry run python main.py
   ```

---

## 💡 Usage Guide

### 📂 Upload Section
- **Multi-File Support**: Select and upload multiple documents at once.
- **Image Processing**: Check the toggle if you want the AI to analyze visual content (graphs/tables) within your PDFs.

### 🔍 Search Section
- **Natural Language Query**: Just type your question and hit **Search**.
- **Context Awareness**: Expand the "Show context" section to see the exact text and images the AI used to build your answer.

### ⚙️ Storage Status (Sidebar)
- **Live Countdown**: Keep track of your session with the countdown timer. 
- **Auto-Refresh**: Each search or upload resets your activity timer!
- **Note**: Data is automatically cleared after user inactivity is detected to keep storage clean.

### 🧹 Clear Storage
- **Instant Reset**: Click the **Clear Storage** button to immediately wipe your session data and reset the uploader for a fresh start.

---

## ☁️ Deployment

Ready to share? This app is fully optimized for **Streamlit Cloud**. Simply connect your GitHub repository, set `main.py` as the entry point, and add your `.env` keys to the **Secrets** manager in TOML format.

---

## 🛡️ License
This project is licensed under the MIT License.

**Enjoy fast, accurate, and intelligent document search!** ✨
