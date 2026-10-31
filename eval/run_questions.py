import time
import requests
import pandas as pd

BASE_URL = "http://127.0.0.1:8000"

df = pd.read_csv("questions.csv")

answers = []
cited_times = []
seconds_taken = []

for _, row in df.iterrows():
    start = time.time()
    resp = requests.post(
        f"{BASE_URL}/ask",
        json={"video_id": row["video_id"], "question": row["question"]},
        timeout=120,
    )
    resp.raise_for_status()
    elapsed = time.time() - start
    data = resp.json()
    answers.append(data["answer"])
    cited_times.append(" | ".join(s["time"] for s in data["sources"]))
    seconds_taken.append(round(elapsed, 1))
    print(f"Row {row['id']} done in {round(elapsed, 1)}s")

df["answer"] = answers
df["cited_times"] = cited_times
df["seconds"] = seconds_taken
df["correct"] = ""
df["cited_ok"] = ""
df["notes"] = ""
df.to_csv("results.csv", index=False)

warm = seconds_taken[1:]
print("First question (builds the index):", seconds_taken[0], "s")
print("Average of the rest:", round(sum(warm) / len(warm), 1), "s")
print("Saved results.csv")