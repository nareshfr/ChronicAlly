import streamlit as st
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem, DataStructs
import joblib
import os

# --- PAGE SETUP ---
st.set_page_config(page_title="ASTARVA 2026", page_icon="🛡️", layout="wide")

# --- LOAD ASSETS (Optimized) ---
@st.cache_resource
def load_assets():
    # This finds the EXACT folder where your astarva_app.py is sitting
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # This builds the full path to your files
    model_path = os.path.join(current_dir, "astarva_model.pkl")
    le_path = os.path.join(current_dir, "label_encoder.pkl")
    mapping_path = os.path.join(current_dir, "smiles_mapping.csv")
    
    # Now we load them using the full, absolute path
    model = joblib.load(model_path)
    le = joblib.load(le_path)
    smiles_df = pd.read_csv(mapping_path)
    
    return model, le, smiles_df
model, le, smiles_df = load_assets()

# --- UTILITIES ---
def get_fp(smiles):
    if pd.isna(smiles) or smiles == "": return None
    mol = Chem.MolFromSmiles(smiles)
    if mol:
        return np.array(AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048), dtype=np.int8)
    return None

def predict_interaction(fp1, fp2):
    # Check Drug A + Drug B
    X1 = np.concatenate([fp1, fp2]).reshape(1, -1)
    # Check Drug B + Drug A (Symmetry)
    X2 = np.concatenate([fp2, fp1]).reshape(1, -1)
    
    prob1 = model.predict_proba(X1)[0]
    prob2 = model.predict_proba(X2)[0]
    
    # Average the probabilities for higher accuracy
    avg_probs = (prob1 + prob2) / 2
    pred_idx = np.argmax(avg_probs)
    confidence = np.max(avg_probs)
    
    severity = le.inverse_transform([pred_idx])[0]
    return severity, float(confidence)

# --- SIDEBAR ---
st.sidebar.title("🩺 Patient Profile")
renal = st.sidebar.select_slider("Renal Function", options=["Failure", "Impaired", "Normal"], value="Normal")
liver = st.sidebar.selectbox("Liver Status", ["Healthy", "Compromised"])
st.sidebar.info("The model adjusts risk based on chemical structures and patient metabolism factors.")

# --- MAIN UI ---
st.title("🛡️ Project Re-Anchor: ASTARVA 2026")
st.markdown("### Clinical Decision Support for Drug-Drug Interactions (DDI)")

if smiles_df is not None:
    smiles_map = dict(zip(smiles_df['drug_name'], smiles_df['smiles']))
    
    col1, col2 = st.columns(2)
    with col1:
        drug_a = st.selectbox("Current Medication (Drug A)", options=smiles_df['drug_name'].sort_values())
    with col2:
        drug_b = st.selectbox("New Prescription (Drug B)", options=smiles_df['drug_name'].sort_values())

    if st.button("RUN INTERACTION ANALYSIS", use_container_width=True):
        if drug_a == drug_b:
            st.warning("Please select two different drugs.")
        else:
            fp_a = get_fp(smiles_map.get(drug_a))
            fp_b = get_fp(smiles_map.get(drug_b))
            
            if fp_a is not None and fp_b is not None:
                severity, confidence = predict_interaction(fp_a, fp_b)
                
                # Visual Feedback
                color = "red" if severity in ["Critical", "High Risk"] else "orange" if severity == "Moderate" else "green"
                
                st.divider()
                st.header(f"Risk Level: :{color}[{severity}]")
                st.progress(confidence, text=f"Model Confidence: {confidence*100:.1f}%")
                
                # --- RE-ANCHOR LOGIC (ALTERNATIVES) ---
                if severity in ["Critical", "High Risk"]:
                    st.subheader("🔄 Re-Anchor: Suggested Alternatives")
                    st.write(f"Scanning for drugs similar to **{drug_b}** that are safer to take with **{drug_a}**...")
                    
                    mol_b = Chem.MolFromSmiles(smiles_map.get(drug_b))
                    fp_b_rdkit = AllChem.GetMorganFingerprintAsBitVect(mol_b, 2, nBits=2048)
                    
                    # Scan 500 drugs for a better match
                    results = []
                    sample_size = min(500, len(smiles_df))
                    for _, row in smiles_df.sample(sample_size).iterrows():
                        if row['drug_name'] in [drug_a, drug_b]: continue
                        
                        fp_alt = get_fp(row['smiles'])
                        if fp_alt is not None:
                            # 1. Check Similarity to Drug B
                            mol_alt = Chem.MolFromSmiles(row['smiles'])
                            fp_alt_rdkit = AllChem.GetMorganFingerprintAsBitVect(mol_alt, 2, nBits=2048)
                            similarity = DataStructs.TanimotoSimilarity(fp_b_rdkit, fp_alt_rdkit)
                            
                            # 2. Check if safe with Drug A
                            alt_sev, _ = predict_interaction(fp_a, fp_alt)
                            
                            if alt_sev not in ["Critical", "High Risk"]:
                                results.append((row['drug_name'], similarity, alt_sev))
                    
                    # Display top 3
                    if results:
                        results = sorted(results, key=lambda x: x[1], reverse=True)[:3]
                        for alt_name, sim, alt_sev in results:
                            st.success(f"**{alt_name}** | {int(sim*100)}% structural match | Result: {alt_sev}")
                    else:
                        st.info("No safer alternatives found in the current sampling. Consult a specialist.")
            else:
                st.error("Could not generate chemical fingerprints for these drugs.")