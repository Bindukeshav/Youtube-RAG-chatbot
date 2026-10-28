import os
import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.2, api_key=os.getenv("GROQ_API_KEY"))

WINDOW_SECONDS = 45
OVERLAP_SECONDS = 10
MAX_QUESTION_CHARS = 500
MAX_DISTANCE = 1.3   # lower = stricter. You will tune this with your test questions.

STORE_CACHE = {}

prompt = PromptTemplate(
    template="""You are a helpful assistant answering questions about a video transcript.
Each context passage starts with a timestamp in [mm:ss]. Use the passages to answer, and mention the timestamp where the topic is explained.
If the context gives partial information, use it to make a reasonable inference and answer helpfully.
Only say you don't know if the context is completely unrelated to the question.

Follow the user's formatting instructions exactly. If they ask for bullet points, use markdown bullet points (lines starting with "- "). If they ask for a numbered list, use "1.", "2.", etc. If they ask for a short answer, keep it to 1-2 sentences. If no format is specified, write a clear, concise paragraph.

Always answer in English, regardless of what language the context or transcript is in.

Context:
{context}

Question: {question}
""",
    input_variables=["context", "question"],
)

class AskRequest(BaseModel):
    video_id: str
    question: str

def fmt(seconds: float) -> str:
    s = int(seconds)
    return f"{s // 60:02d}:{s % 60:02d}"

def build_chunks(snippets, window=WINDOW_SECONDS, overlap=OVERLAP_SECONDS):
    """Sliding window over time: 45s chunks, each starting 35s after the last."""
    end_time = snippets[-1].start + snippets[-1].duration
    step = window - overlap
    chunks, start = [], 0.0
    while start < end_time:
        end = start + window
        text = " ".join(s.text for s in snippets if start <= s.start < end).strip()
        if text:
            chunks.append(Document(
                page_content=text,
                metadata={"start": start, "end": min(end, end_time)},
            ))
        start += step
    return chunks

def get_store(video_id: str):
    if video_id in STORE_CACHE:
        return STORE_CACHE[video_id]

    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        raise ValueError("That doesn't look like a valid YouTube video ID.")

    try:
        fetched = YouTubeTranscriptApi().fetch(video_id, languages=["en", "en-US", "en-GB", "hi"])
    except (TranscriptsDisabled, NoTranscriptFound):
        raise ValueError("This video has no captions in a supported language (English or Hindi).")
    except Exception:
        raise RuntimeError("Could not fetch the transcript right now. Please try again.")

    snippets = list(fetched)
    if not snippets:
        raise ValueError("The transcript for this video is empty.")

    store = FAISS.from_documents(build_chunks(snippets), embeddings)
    STORE_CACHE[video_id] = store
    return store

def retrieve(video_id: str, question: str, k: int = 6):
    """Returns [(Document, distance), ...] sorted best first. Used by the API and the eval script."""
    store = get_store(video_id)
    return store.similarity_search_with_score(question, k=k)

@app.post("/ask")
def ask(req: AskRequest):
    q = req.question.strip()
    if not q:
        return {"answer": "Please type a question.", "sources": []}
    if len(q) > MAX_QUESTION_CHARS:
        return {"answer": f"That question is too long. Please keep it under {MAX_QUESTION_CHARS} characters.", "sources": []}

    try:
        results = retrieve(req.video_id, q, k=6)
    except ValueError as e:
        return {"answer": str(e), "sources": []}
    except Exception:
        return {"answer": "Something went wrong while reading the video. Please try again.", "sources": []}

    relevant = [(d, s) for d, s in results if s <= MAX_DISTANCE]
    if not relevant:
        return {"answer": "I couldn't find anything about that in this video.", "sources": []}

    context = "\n\n".join(f"[{fmt(d.metadata['start'])}] {d.page_content}" for d, _ in relevant)
    try:
        answer = llm.invoke(prompt.invoke({"context": context, "question": q}))
    except Exception:
        return {"answer": "The AI service is not responding right now. Please try again in a moment.", "sources": []}

    sources = [
        {
            "time": fmt(d.metadata["start"]),
            "link": f"https://youtu.be/{req.video_id}?t={int(d.metadata['start'])}",
        }
        for d, _ in relevant[:3]
    ]
    return {"answer": answer.content, "sources": sources}

@app.get("/health")
def health():
    return {"status": "ok"}
