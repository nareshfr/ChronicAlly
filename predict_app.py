import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
import joblib
import warnings

# Mute RDKit warnings for a cleaner UI
warnings.filterwarnings("ignore")

# 1. LOAD THE TRAINED COMPONENTS
print("Loading Engine...")
model = joblib.load("ChronicAlly/astarva_model.pkl")
le = joblib.load("ChronicAlly/label_encoder.pkl")
smiles_df = pd.read_csv("ChronicAlly/smiles_mapping.csv")
smiles_map = dict(zip(smiles_df['drug_name'], smiles_df['smiles']))

# 2. UTILITY: TURN NAME INTO FINGERPRINT
def get_fp(drug_name):
    smiles = smiles_map.get(drug_name)
    if not smiles:
        # If drug not in our list, we could add an API lookup here later!
        return None
    
    mol = Chem.MolFromSmiles(smiles)
    if mol:
        return np.array(AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048), dtype=np.int8)
    return None

# 3. PREDICTION FUNCTION
def check_interaction(drug1, drug2):
    fp1 = get_fp(drug1)
    fp2 = get_fp(drug2)
    
    if fp1 is None or fp2 is None:
        return "Error: One or both drugs not found in chemical database."

    # Combine: 2048 + 2048 = 4096 features
    X_input = np.concatenate([fp1, fp2]).reshape(1, -1)
    
    # Get prediction and probabilities
    pred_idx = model.predict(X_input)[0]
    probs = model.predict_proba(X_input)[0]
    
    severity = le.inverse_transform([pred_idx])[0]
    confidence = np.max(probs) * 100
    
    return f"RESULT: {severity} ({confidence:.1f}% Confidence)"

# 4. SIMPLE INTERACTIVE LOOP
print("\n--- Project Re-Anchor: ASTARVA 2026 CDSS ---")
print("Type 'exit' to quit.\n")

while True:
    d1 = input("Enter First Drug: ").strip()
    if d1.lower() == 'exit': break
    
    d2 = input("Enter Second Drug: ").strip()
    if d2.lower() == 'exit': break
    
    result = check_interaction(d1, d2)
    print(f"\n>>> {result}\n" + "-"*40)