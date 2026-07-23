import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
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

CACHE = {}
CHUNK_CACHE = {}

prompt = PromptTemplate(
    template="""You are a helpful assistant answering questions about a video transcript.
Use the provided context to answer as best you can. If the context gives partial information, use it to make a reasonable inference and answer helpfully.
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

def get_retriever(video_id: str):
    if video_id in CACHE:
        return CACHE[video_id]

    ytt_api = YouTubeTranscriptApi()
    try:
        fetched = ytt_api.fetch(video_id, languages=["en", "en-US", "en-GB", "hi"])
    except (TranscriptsDisabled, NoTranscriptFound):
        raise Exception("This video has no captions/transcript available. Try a different video.")

    transcript = " ".join(s.text for s in fetched)

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.create_documents([transcript])
    CHUNK_CACHE[video_id] = chunks

    vector_store = FAISS.from_documents(chunks, embeddings)
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 6})
    CACHE[video_id] = retriever
    return retriever

@app.post("/ask")
def ask(req: AskRequest):
    try:
        retriever = get_retriever(req.video_id)
        docs = retriever.invoke(req.question)
        context = "\n\n".join(d.page_content for d in docs)
        if req.video_id in CHUNK_CACHE:
            first_chunk = CHUNK_CACHE[req.video_id][0].page_content
            if first_chunk not in context:
                context = first_chunk + "\n\n" + context
        final_prompt = prompt.invoke({"context": context, "question": req.question})
        answer = llm.invoke(final_prompt)
        return {"answer": answer.content}
    except Exception as e:
        return {"answer": f"Error: {str(e)}"}

@app.get("/health")
def health():
    return {"status": "ok"}