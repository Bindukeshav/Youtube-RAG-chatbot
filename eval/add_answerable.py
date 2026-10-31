import pandas as pd

df = pd.read_csv("questions.csv")

if "answerable" not in df.columns:
    df["answerable"] = "yes"

df.to_csv("questions.csv", index=False)
print(df[["id", "answerable"]])