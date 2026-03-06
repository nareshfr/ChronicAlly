from flask import Flask,request,jsonify
import itertools
import pandas as pd

from model import predict_interaction
from utils import adjust_patient_risk

app = Flask(__name__)

smiles_df = pd.read_csv("smiles_mapping.csv")

smiles_map = dict(zip(smiles_df["drug_name"],smiles_df["smiles"]))


@app.route("/predict",methods=["POST"])
def predict():

    data = request.json

    drugs = data["drugs"]
    patient = data["patient"]

    pairs = list(itertools.combinations(drugs,2))

    results = []

    for d1,d2 in pairs:

        smiles1 = smiles_map.get(d1)
        smiles2 = smiles_map.get(d2)

        ai_sev,conf = predict_interaction(smiles1,smiles2)

        final_sev,reasons = adjust_patient_risk(ai_sev,patient)

        results.append({

            "drug_pair":[d1,d2],
            "ai_severity":ai_sev,
            "final_severity":final_sev,
            "confidence":conf,
            "patient_factors":reasons

        })

    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)