import pandas as pd

df = pd.read_csv("results.csv")
df["verified"] = df["verified"].astype("object")
df["notes"] = df["notes"].astype("object")

for i, row in df.iterrows():
    print("=" * 60)
    print(f"Row {row['id']}: {row['question']}")
    print("A:", row["answer"])
    verdict = input("verified (yes/no/partial, Enter to skip): ").strip().lower()
    if verdict == "":
        continue
    note = input("notes: ").strip()
    df.at[i, "verified"] = verdict
    df.at[i, "notes"] = note

df.to_csv("results_checked.csv", index=False)
print(df["verified"].value_counts())