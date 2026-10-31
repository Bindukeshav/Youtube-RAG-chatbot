import pandas as pd

df = pd.read_csv("results.csv")

def to_link(video_id, time_text):
    parts = [int(p) for p in time_text.split(":")]
    seconds = 0
    for p in parts:
        seconds = seconds * 60 + p
    return f"https://youtu.be/{video_id}?t={seconds}"

for _, row in df.iterrows():
    print("=" * 60)
    print(f"Row {row['id']} | {row['label']}")
    print("Q:", row["question"])
    print("A:", row["answer"])
    print("V:", row["verified"])
    print("N:", row["notes"])
    times = str(row["cited_times"])
    if times != "nan":
        for t in times.split(" | "):
            print("  ", t, to_link(row["video_id"], t))