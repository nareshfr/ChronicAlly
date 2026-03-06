import joblib
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem

model = joblib.load("astarva_model.pkl")
# Set device to CPU for thread-safe inference in the Flask server
model.set_params(device='cpu')
le = joblib.load("label_encoder.pkl")


def get_fp(smiles):

    mol = Chem.MolFromSmiles(smiles)

    if mol:
        return np.array(
            AllChem.GetMorganFingerprintAsBitVect(mol,2,nBits=2048),
            dtype=np.int8
        )

    return None


def predict_interaction(smiles1, smiles2):

    fp1 = get_fp(smiles1)
    fp2 = get_fp(smiles2)

    if fp1 is None or fp2 is None:
        return "Unknown",0

    X1 = np.concatenate([fp1,fp2]).reshape(1,-1)
    X2 = np.concatenate([fp2,fp1]).reshape(1,-1)

    prob1 = model.predict_proba(X1)[0]
    prob2 = model.predict_proba(X2)[0]

    avg_prob = (prob1 + prob2) / 2

    idx = np.argmax(avg_prob)

    severity = le.inverse_transform([idx])[0]

    confidence = float(np.max(avg_prob))

    return severity, confidence