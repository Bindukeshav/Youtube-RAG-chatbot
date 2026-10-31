import pandas as pd

df = pd.read_csv("results_checked.csv")


def is_yes(column):
    return df[column].fillna("").astype(str).str.lower().str.strip() == "yes"


def percent(part, whole):
    return round(100 * part / whole, 1) if whole else None


df["is_answerable"] = is_yes("answerable")
df["is_correct"] = is_yes("correct")
df["is_cited_ok"] = is_yes("cited_ok")

phrases = ["doesn't clearly cover", "couldn't find anything"]
df["refused"] = df["answer"].fillna("").apply(lambda text: any(p in text for p in phrases))

answerable = df[df["is_answerable"]]
unanswerable = df[~df["is_answerable"]]
answered = answerable[~answerable["refused"]]
refusals = df[df["refused"]]

print("Questions:", len(df), "| videos:", df["video_id"].nunique())
print("Answerable:", len(answerable), "| Unanswerable:", len(unanswerable))
print("Answer accuracy (%):", percent(answerable["is_correct"].sum(), len(answerable)))
print("Citation accuracy (%):", percent(answered["is_cited_ok"].sum(), len(answered)))
print("Refusal recall (%):", percent(unanswerable["refused"].sum(), len(unanswerable)))
print("Refusal precision (%):", percent((~refusals["is_answerable"]).sum(), len(refusals)))
if "seconds" in df.columns:
    print("Median response time (s):", round(df["seconds"].median(), 1))