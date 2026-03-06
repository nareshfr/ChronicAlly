from flask import Flask, request, jsonify

from interaction_engine import check_interaction
from model import predict_severity
from utils import generate_pairs, adjust_for_patient
from recoomender import suggest_alternative

app = Flask(__name__)

@app.route("/predict", methods=["POST"])
def predict():

    data = request.json

    drugs = data["drugs"]
    age = data["age"]

    pairs = generate_pairs(drugs)

    results = []

    for d1, d2 in pairs:

        desc = check_interaction(d1, d2)

        severity = predict_severity(desc)

        severity = adjust_for_patient(severity, age)

        alt = suggest_alternative(d1)

        results.append({
            "drug_pair":[d1,d2],
            "interaction":desc,
            "severity":severity,
            "alternatives":alt
        })

    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)