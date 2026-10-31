import pandas as pd

df = pd.read_csv("results.csv")

for col in ["correct", "cited_ok", "notes"]:
    if col not in df.columns:
        df[col] = ""
    df[col] = df[col].astype("object")

REFUSALS = ["doesn't clearly cover", "couldn't find anything"]


def to_link(video_id, time_text):
    seconds = 0
    for part in time_text.split(":"):
        seconds = seconds * 60 + int(part)
    return f"https://youtu.be/{video_id}?t={seconds}"


def ask_yes_no(message):
    while True:
        reply = input(message + " (y/n): ").strip().lower()
        if reply in ("y", "n"):
            return "yes" if reply == "y" else "no"
        print("Please type y or n.")


for i, row in df.iterrows():
    print("=" * 60)
    print(f"Row {row['id']} | video {row['video_id']} | answerable: {row['answerable']}")
    print("Q:", row["question"])
    print("A:", row["answer"])

    refused = any(p in str(row["answer"]) for p in REFUSALS)
    times = str(row["cited_times"])
    if times != "nan" and times.strip():
        for t in times.split(" | "):
            print("  link:", to_link(row["video_id"], t))

    if str(row["answerable"]).strip().lower() != "yes":
        print("(Not answerable, so no verdict needed.)")
        continue

    if refused:
        df.at[i, "correct"] = "no"
        print("(Bot refused a question the video answers, so correct = no.)")
    else:
        df.at[i, "correct"] = ask_yes_no("Is the answer correct?")
        df.at[i, "cited_ok"] = ask_yes_no("Does the link land on the right moment?")

    note = input("notes (Enter to skip): ").strip()
    if note:
        df.at[i, "notes"] = note

    df.to_csv("results_checked.csv", index=False)

df.to_csv("results_checked.csv", index=False)
print("Saved results_checked.csv")