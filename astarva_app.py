import streamlit as st
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem, DataStructs
import joblib
import os
import itertools

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="Chronic Ally", page_icon="🛡️", layout="wide")

# --- 2. LOAD ASSETS (Optimized Caching) ---
@st.cache_resource
def load_assets():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, "astarva_model.pkl")
    le_path = os.path.join(current_dir, "label_encoder.pkl")
    mapping_path = os.path.join(current_dir, "smiles_mapping.csv")
    
    model = joblib.load(model_path)
    le = joblib.load(le_path)
    smiles_df = pd.read_csv(mapping_path)
    return model, le, smiles_df

model, le, smiles_df = load_assets()

# --- 3. LOGIC FUNCTIONS ---
@st.cache_data
def get_fp(smiles):
    if pd.isna(smiles) or smiles == "": return None
    mol = Chem.MolFromSmiles(smiles)
    if mol:
        return np.array(AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048), dtype=np.int8)
    return None

def predict_interaction(fp1, fp2):
    X1 = np.concatenate([fp1, fp2]).reshape(1, -1)
    X2 = np.concatenate([fp2, fp1]).reshape(1, -1) # Symmetry
    
    prob1 = model.predict_proba(X1)[0]
    prob2 = model.predict_proba(X2)[0]  
    
    avg_probs = (prob1 + prob2) / 2
    pred_idx = np.argmax(avg_probs)
    confidence = np.max(avg_probs)
    
    severity = le.inverse_transform([pred_idx])[0]
    return severity, float(confidence)

def get_final_verdict(ai_severity, p):
    severity_order = ["Minor", "Moderate", "High Risk", "Critical"]
    try:
        current_idx = severity_order.index(ai_severity)
    except:
        current_idx = 0

    reasons = []

    # Pregnancy Check
    if p["is_pregnant"]:
        current_idx = max(current_idx, 2)
        reasons.append("Pregnancy: Fetal safety priority. Automatic risk elevation.")
        if ai_severity == "High Risk": current_idx = 3

    # Age Check
    if p["age"] >= 65:
        current_idx = min(current_idx + 1, 3)
        reasons.append("Geriatric (65+): Reduced renal clearance & physiological reserve.")

    # Disease Specifics
    if p["diabetes"] and ai_severity == "Moderate":
        current_idx = 2
        reasons.append("Diabetes: High risk for metabolic/glycemic instability.")

    if p["heart"] and ai_severity == "High Risk":
        current_idx = 3
        reasons.append("Heart Condition: Risk of cardiac strain/Arrhythmia.")

    if p["asthma"] and ai_severity in ["Moderate", "High Risk"]:
        current_idx = min(current_idx + 1, 3)
        reasons.append("Asthma/COPD: Respiratory depressant risk.")

    if p["renal"] != "Normal" or p["liver"] != "Healthy":
        if current_idx < 3: current_idx += 1
        reasons.append(f"Organ Impairment ({p['renal']}/{p['liver']}): Slower drug metabolism.")

    return severity_order[current_idx], reasons

# --- 4. SIDEBAR ---
st.sidebar.title("🩺 Patient Profile")
age_val = st.sidebar.number_input("Patient Age", 0, 120, 25)
gender_val = st.sidebar.radio("Gender", ["Male", "Female", "Other"])
renal_val = st.sidebar.select_slider("Renal Function", ["Failure", "Impaired", "Normal"], "Normal")
liver_val = st.sidebar.selectbox("Liver Status", ["Healthy", "Compromised"])

preg_val = False
if gender_val == "Female":
    preg_val = st.sidebar.checkbox("Is Pregnant?")

st.sidebar.markdown("---")
st.sidebar.header("🏥 Medical History")
db_val = st.sidebar.checkbox("Diabetes")
asthma_val = st.sidebar.checkbox("Asthma / COPD")
heart_val = st.sidebar.checkbox("Heart Condition")

patient_data = {
    "age": age_val, "is_pregnant": preg_val, "diabetes": db_val,
    "asthma": asthma_val, "heart": heart_val, "renal": renal_val, "liver": liver_val
}

# --- 5. MAIN UI ---
st.title("🛡️ Project Re-Anchor: ASTARVA 2026")
st.markdown("### Clinical Decision Support for Polypharmacy")



if smiles_df is not None:
    smiles_map = dict(zip(smiles_df['drug_name'], smiles_df['smiles']))
    selected_drugs = st.multiselect("Medication List:", options=smiles_df['drug_name'].sort_values())

    if st.button("RUN MULTI-DRUG ANALYSIS", use_container_width=True):
        if len(selected_drugs) < 2:
            st.warning("Please select at least two drugs.")
        else:
            with st.status("Analyzing Interactions...", expanded=True) as status:
                drug_pairs = list(itertools.combinations(selected_drugs, 2))
                all_results = []
                highest_severity_idx = 0
                severity_order = ["Minor", "Moderate", "High Risk", "Critical"]

                for drug_a, drug_b in drug_pairs:
                    fp_a, fp_b = get_fp(smiles_map.get(drug_a)), get_fp(smiles_map.get(drug_b))
                    if fp_a is not None and fp_b is not None:
                        raw_sev, conf = predict_interaction(fp_a, fp_b)
                        final_sev, reasons = get_final_verdict(raw_sev, patient_data)
                        
                        curr_idx = severity_order.index(final_sev)
                        if curr_idx > highest_severity_idx: highest_severity_idx = curr_idx
                        
                        all_results.append({"pair": (drug_a, drug_b), "severity": final_sev, "reasons": reasons})
                
                status.update(label="Analysis Complete!", state="complete", expanded=False)

            # --- DISPLAY RESULTS ---
            overall_sev = severity_order[highest_severity_idx]
            color = "red" if overall_sev in ["Critical", "High Risk"] else "orange" if overall_sev == "Moderate" else "green"
            st.header(f"Overall Regimen Risk: :{color}[{overall_sev}]")

            for res in all_results:
                d_a, d_b = res['pair']
                with st.expander(f"Detail: {d_a} + {d_b} ({res['severity']})"):
                    if res['reasons']:
                        for r in res['reasons']: st.write(f"• {r}")
                    
                    # --- RE-ANCHOR SUGGESTIONS ---
                    if res['severity'] in ["Critical", "High Risk"]:
                        st.markdown("---")
                        st.subheader(f"🔄 Re-Anchor Alternatives for {d_b}")
                        
                        mol_b = Chem.MolFromSmiles(smiles_map.get(d_b))
                        fp_b_rdkit = AllChem.GetMorganFingerprintAsBitVect(mol_b, 2, nBits=2048)
                        
                        alts = []
                        # Sample 300 for speed
                        for _, row in smiles_df.sample(min(300, len(smiles_df))).iterrows():
                            if row['drug_name'] in selected_drugs: continue
                            fp_alt = get_fp(row['smiles'])
                            if fp_alt is not None:
                                # Similarity check
                                mol_alt = Chem.MolFromSmiles(row['smiles'])
                                fp_alt_rdkit = AllChem.GetMorganFingerprintAsBitVect(mol_alt, 2, nBits=2048)
                                sim = DataStructs.TanimotoSimilarity(fp_b_rdkit, fp_alt_rdkit)
                                
                                # Safety check
                                a_sev, _ = predict_interaction(fp_a, fp_alt)
                                f_a_sev, _ = get_final_verdict(a_sev, patient_data)
                                
                                if f_a_sev not in ["Critical", "High Risk"]:
                                    alts.append((row['drug_name'], sim, f_a_sev))
                        
                        if alts:
                            alts = sorted(alts, key=lambda x: x[1], reverse=True)[:2]
                            for name, sim, s_level in alts:
                                st.success(f"**{name}** ({int(sim*100)}% Match) - Safer Option")