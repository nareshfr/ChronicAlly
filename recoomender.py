import pandas as pd

df = pd.read_csv("data/db_drug_interactions.csv")

def suggest_alternative(drug):

    alternatives = df[df["Drug 1"] != drug]["Drug 1"].unique()

    return list(alternatives[:3])