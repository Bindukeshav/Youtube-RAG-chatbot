import pandas as pd

pd.set_option("display.max_colwidth", None)
df = pd.read_csv("questions.csv")
print(df.shape)
print(df[["id", "timestamp_sec", "label"]])