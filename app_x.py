from flask import Flask,request,jsonify
from flask_cors import CORS
import itertools
import pandas as pd

from model import predict_interaction
from utils import adjust_patient_risk

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

smiles_df = pd.read_csv("smiles_mapping.csv")

# Create a case-insensitive lookup map
smiles_map = {row["drug_name"].lower(): row["smiles"] for _, row in smiles_df.iterrows()}


@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "online", "message": "MedGuard AI ML Backend is running. Use POST /predict for inference."})


@app.route("/predict",methods=["POST"])
def predict():

    data = request.json

    drugs = data["drugs"]
    patient = data["patient"]

    pairs = list(itertools.combinations(drugs,2))

    results = []

    for d1,d2 in pairs:

        smiles1 = smiles_map.get(d1.lower())
        smiles2 = smiles_map.get(d2.lower())

        if not smiles1 or not smiles2 or pd.isna(smiles1) or pd.isna(smiles2):
            ai_sev, conf = "Unknown", 0.0
            final_sev, reasons = "Unknown", ["Missing chemical structure data for one or both drugs."]
        else:
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