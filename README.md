# YouTube Doubt Solver

A Chrome extension that lets you ask questions about any YouTube video and get instant, transcript-grounded answers — no more scrubbing through long videos to find the part you need.

## How it works

This is a Retrieval-Augmented Generation (RAG) pipeline:

1. **Transcript fetch** — pulls the video's captions using `youtube-transcript-api`
2. **Chunking** — splits the transcript into overlapping chunks using LangChain's text splitter
3. **Embedding** — converts each chunk into a vector using `sentence-transformers` (all-MiniLM-L6-v2), run locally
4. **Vector storage & retrieval** — stores chunks in FAISS and retrieves the most relevant ones for a given question via similarity search
5. **Generation** — passes the question + retrieved context to Llama 3.1 (hosted via Groq) to generate a grounded answer

## Tech stack

- **Backend:** FastAPI, LangChain, FAISS, sentence-transformers, Groq API (Llama 3.1)
- **Frontend:** Chrome Extension (Manifest V3), vanilla JS/HTML/CSS

## Project structure
├── backend/
│ ├── main.py # FastAPI server + RAG pipeline
│ └── requirements.txt # Python dependencies
└── extension/
├── manifest.json # Chrome extension config
├── popup.html # Extension UI
├── popup.js # Extension logic
└── icon.png

## Setup & run locally

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

Create a `.env` file inside `backend/` with:


GROQ_API_KEY=your_groq_api_key_here

(Get a free key at https://console.groq.com/keys)

Start the server:
```bash
python -m uvicorn main:app --reload --port 8000
```

### Chrome Extension

1. Go to `chrome://extensions`
2. Enable **Developer mode** (top right)
3. Click **Load unpacked**
4. Select the `extension` folder

Make sure the backend server is running, then open any YouTube video, click the extension icon, and ask a question.

## Future improvements

- Ragas / LangSmith evaluation (faithfulness, answer relevancy, context precision, context recall)
- Hybrid retrieval + reranking
- Multi-query generation and query rewriting
- Deploy backend for use without running locally

## Demo

*(add a screen recording or GIF here)*


(Get a free key at https://console.groq.com/keys)

Start the server:
```bash
python -m uvicorn main:app --reload --port 8000
```

### Chrome Extension

1. Go to `chrome://extensions`
2. Enable **Developer mode** (top right)
3. Click **Load unpacked**
4. Select the `extension` folder

Make sure the backend server is running, then open any YouTube video, click the extension icon, and ask a question.

## Future improvements

- Ragas / LangSmith evaluation (faithfulness, answer relevancy, context precision, context recall)
- Hybrid retrieval + reranking
- Multi-query generation and query rewriting
- Deploy backend for use without running locally

## Demo

*(add a screen recording or GIF here)*
