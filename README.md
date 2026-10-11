cat > README.md <<'EOF'
# 🎥 YouTube RAG Chatbot

A Chrome extension with a FastAPI backend that answers natural-language questions about a YouTube video using retrieval-augmented generation (RAG).

![Screenshot](screenshot.png)

## How it works

1. The extension sends the video link and your question to the FastAPI backend.
2. The backend fetches the video transcript and splits it into chunks.
3. Chunks are embedded with Sentence-Transformers and indexed in FAISS.
4. The most relevant chunks are retrieved and passed to a Groq-hosted LLM, which writes the answer.

## Tech Stack

- **FastAPI** for the backend API
- **LangChain** for text splitting and prompt/LLM orchestration
- **FAISS** for vector search over transcript chunks
- **Sentence-Transformers** for embeddings
- **Groq** (Llama 3.1 8B Instant) for answer generation
- **Chrome Extension** (JavaScript) for the user interface on YouTube pages

## Project Structure
├── backend/ # FastAPI app (main.py)
├── extension/ # Chrome extension
├── requirements.txt
├── .env.example
└── README.md


## Setup

1. Clone the repo
```bash
git clone https://github.com/Bindukeshav/Youtube-RAG-chatbot.git
cd Youtube-RAG-chatbot
```
2. Install dependencies
```bash
pip install -r requirements.txt
```
3. Copy `.env.example` to `.env` and add your Groq API key
4. Start the backend
```bash
cd backend
python -m uvicorn main:app --reload
```
5. Open `chrome://extensions`, enable Developer mode, click **Load unpacked**, and select the `extension` folder

## Limitations

- Only works on videos that have a transcript or captions.
- Very long videos take longer to index.
- Answers are limited to what is in the transcript.
EOF
