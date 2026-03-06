import pandas as pd

import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(BASE_DIR, "data", "db_drug_interactions.csv")

df = pd.read_csv(file_path)
# clean drug names
df["Drug 1"] = df["Drug 1"].str.lower()
df["Drug 2"] = df["Drug 2"].str.lower()

def check_interaction(drug_a, drug_b):

    drug_a = drug_a.lower()
    drug_b = drug_b.lower()

    result = df[
        ((df["Drug 1"] == drug_a) & (df["Drug 2"] == drug_b)) |
        ((df["Drug 1"] == drug_b) & (df["Drug 2"] == drug_a))
    ]

    if not result.empty:
        return result.iloc[0]["Interaction Description"]
    
    return "No known interaction"