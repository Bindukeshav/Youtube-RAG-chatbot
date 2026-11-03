import os
import traceback

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq

# Use the community implementation available in the project's dependencies.
from langchain_community.embeddings import FastEmbedEmbeddings, HuggingFaceEmbeddings
print("DEBUG groq-related env names:", [k for k in os.environ if "GROQ" in k.upper()], flush=True)
print("DEBUG GROQ_API_KEY set:", bool(os.getenv("GROQ_API_KEY")), flush=True)
# Reads GROQ_API_KEY (and GROQ_MODEL, if you add it) from your .env file.
load_dotenv()

# ---------- Settings you can tune ----------
MAX_QUESTION_CHARS = 500   # longest question accepted
MAX_DISTANCE = 1.3         # lower = stricter; use /debug to tune it
WINDOW = 10                # transcript lines joined into one chunk
STRIDE = 6                 # step between chunks (chunks overlap by 4 lines)
MODEL_NAME = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

app = FastAPI()

# Lets the browser extension call this server without being blocked.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    video_id: str
    question: str


# The embedding model turns text into numbers so similar meanings are close together.
embeddings = FastEmbedEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# temperature=0 keeps answers consistent; max_tokens caps the reply length.
llm = ChatGroq(model=MODEL_NAME, temperature=0, max_tokens=1500)
prompt = ChatPromptTemplate.from_template(
    """You answer questions about a YouTube video using only the transcript excerpts below.

Rules:
- Answer the question directly in one to three sentences, in your own words. Never copy transcript lines.
- The transcript is auto-generated and messy (filler words, broken sentences). Clean it up.
- After each claim, cite the timestamp in square brackets, like [00:23]. Use only timestamps that appear in the excerpts.
- If the excerpts do not answer the question, reply exactly: This video doesn't clearly cover that.

Transcript excerpts:
{context}

Question: {question}

Answer:"""
)

# One search index per video, so each transcript is downloaded and embedded only once.
indexes = {}


def fmt(seconds):
    """Turn seconds into MM:SS, or H:MM:SS for videos over an hour."""
    s = int(seconds)
    hours, rest = divmod(s, 3600)       # divmod gives (quotient, remainder)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def build_index(video_id):
    """Download the transcript, cut it into chunks, and build a searchable index."""
    if video_id in indexes:
        return indexes[video_id]

    try:
        transcript = list(YouTubeTranscriptApi().fetch(video_id))
    except Exception:
        traceback.print_exc()
        raise ValueError("I couldn't get a transcript for this video. Captions may be turned off.")
    if not transcript:
        raise ValueError("This video has an empty transcript.")

    docs = []
    for i in range(0, len(transcript), STRIDE):
        window = transcript[i:i + WINDOW]
        text = " ".join(item.text.replace("\n", " ") for item in window)
        docs.append(Document(page_content=text, metadata={"start": window[0].start}))

    indexes[video_id] = FAISS.from_documents(docs, embeddings)
    return indexes[video_id]


def retrieve(video_id, question, k=6):
    """Return the k chunks closest in meaning to the question, as (doc, distance) pairs."""
    store = build_index(video_id)
    return store.similarity_search_with_score(question, k=k)


@app.get("/health")
def health():
    """Open http://127.0.0.1:8000/health in a browser to check the server is up."""
    return {"status": "ok", "model": MODEL_NAME}


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
        traceback.print_exc()
        return {"answer": "Something went wrong while reading the video. Please try again.", "sources": []}

    relevant = [(d, s) for d, s in results if s <= MAX_DISTANCE]
    if not relevant:
        return {"answer": "I couldn't find anything about that in this video.", "sources": []}

    # Put the chunks in video order so the model reads them like a story.
    relevant.sort(key=lambda pair: pair[0].metadata["start"])
    context = "\n\n".join(f"[{fmt(d.metadata['start'])}] {d.page_content}" for d, _ in relevant)

    try:
        answer = llm.invoke(prompt.invoke({"context": context, "question": q}))
    except Exception as e:
        print("GROQ ERROR:", repr(e))
        traceback.print_exc()
        return {"answer": "The AI service is not responding right now. Please try again in a moment.", "sources": []}

    if "doesn't clearly cover" in answer.content:
        return {"answer": answer.content, "sources": []}

    sources = [
        {
            "time": fmt(d.metadata["start"]),
            "link": f"https://youtu.be/{req.video_id}?t={int(d.metadata['start'])}",
        }
        for d, _ in relevant[:3]
    ]
    cited = [s for s in sources if s["time"] in answer.content]
    return {"answer": answer.content, "sources": cited or sources[:1]}


@app.post("/debug")
def debug(req: AskRequest):
    """Shows what retrieval returns, before the distance filter and without the AI."""
    try:
        results = retrieve(req.video_id, req.question, k=6)
    except Exception as e:
        return {"error": str(e)}
    return [
        {
            "time": fmt(d.metadata["start"]),
            "distance": round(float(s), 3),
            "kept": bool(s <= MAX_DISTANCE),
            "text": d.page_content[:120],
        }
        for d, s in results
    ]