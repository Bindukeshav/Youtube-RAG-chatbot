# YouTube Video Q&A Chatbot (RAG)

Ask questions about any YouTube video and get answers grounded in its transcript. If the answer is not in the video, the bot says so instead of making something up.

![Demo](demo.gif)
<!-- Replace demo.gif with your recording (30-60 seconds of the extension answering a question) -->

## Features

- Answers questions using only the video's transcript (retrieval-augmented generation)
- "Not found" fallback for questions the video does not answer, so it does not hallucinate
- FastAPI backend with a simple `/ask` endpoint
- Chrome extension: ask questions directly on the YouTube page
- Evaluation scripts and a 15-question test set included

## How it works

```
YouTube video ID
      |
      v
Fetch transcript -> split into chunks -> embed (Sentence-Transformers)
      |
      v
Store in FAISS vector index
      |
Question -> embed -> retrieve top matching chunks
      |
      v
LLM (Groq) answers from the retrieved chunks only
      |
      v
Answer + sources (or "I couldn't find anything about that in this video.")
```

## Tech stack

Python, FastAPI, LangChain, FAISS, Sentence-Transformers, Groq LLM API, JavaScript (Chrome extension)

## Project structure

```
Youtube-RAG-chatbot/
├── backend/          # FastAPI app (main.py)
├── extension/        # Chrome extension (manifest.json, popup.html, popup.js)
├── eval/             # Evaluation: questions.csv, run_questions.py, check_eval.py, metrics.py
├── requirements.txt
└── .env.example      # Copy to .env and add your API key
```

## Setup

**1. Clone and install**

```bash
git clone https://github.com/Bindukeshav/Youtube-RAG-chatbot.git
cd Youtube-RAG-chatbot
python -m venv .venv
source .venv/Scripts/activate      # Windows (Git Bash). On Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

**2. Add your API key**

Copy `.env.example` to `.env` and fill in your Groq API key:

```bash
cp .env.example .env
```

**3. Run the backend**

```bash
cd backend
uvicorn main:app --reload
```

Open http://127.0.0.1:8000/docs to try the API in Swagger.

**4. Load the Chrome extension**

1. Open `chrome://extensions`
2. Turn on **Developer mode** (top right)
3. Click **Load unpacked** and select the `extension/` folder
4. Open any YouTube video, click the extension icon and ask a question

## API

`POST /ask`

```json
{
  "video_id": "6yl3NQwG9Mc",
  "question": "What is the silliest rumor Mira has heard about herself?"
}
```

Response:

```json
{
  "answer": "...",
  "sources": [...]
}
```

The `video_id` is the part of the YouTube URL after `v=` (and before any `&`).

## Evaluation

I tested the bot on a 15-question set built from one interview video: 11 questions the video answers and 4 it does not.

| Metric | Result |
|---|---|
| Overall accuracy | **86.7%** (13/15) |
| Answerable questions answered | **81.8%** (9/11) |
| Unanswerable questions correctly declined | **100%** (4/4) |
| Average response time | **~1.2 s** |

Run it yourself:

```bash
cd eval
python run_questions.py     # sends questions.csv to /ask, writes results.csv
python check_eval.py        # compares answers with expected results
python metrics.py           # prints the metrics
```

## Limitations

- Two answerable questions were missed. One needed facts spread across different parts of the transcript (children's ages), and one used a phrase that appears only once in a long passage ("red line").
- The test set is small and uses a single video, so the numbers are indicative, not a benchmark.
- Works only for videos that have a transcript or captions available.

## Future improvements

- Hybrid search (keyword + vector) to catch exact phrases
- Larger evaluation set across several videos and languages
- Tune chunk size and overlap, and the number of retrieved chunks
- Show timestamps so answers link back to the exact moment in the video

## Author

**Bindu K** · [GitHub](https://github.com/Bindukeshav) · [LinkedIn](https://linkedin.com/in/bindu-keshav-380b34425)
