import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
import joblib

# 1. LOAD DATA
print("Step 1: Loading data...")
df = pd.read_csv("ChronicAlly/db_drug_interactions.csv")
smiles_df = pd.read_csv("ChronicAlly/smiles_mapping.csv")

# 2. IMPROVED SEVERITY EXTRACTOR (Detects more categories)
def encode_severity(text):
    text = str(text).lower()
    if any(w in text for w in ['fatal', 'contraindicated', 'severe risk']): return "Critical"
    if 'increase' in text: return "High Risk"
    if 'decrease' in text: return "Moderate"
    if any(w in text for w in ['monitor', 'caution']): return "Minor"
    return "Unknown"

df['severity_text'] = df['Interaction Description'].apply(encode_severity)

# 3. LABEL FIXER
le = LabelEncoder()
y = le.fit_transform(df['severity_text'])
num_unique_classes = len(le.classes_)
print(f"Detected {num_unique_classes} unique risk levels: {le.classes_}")

# 4. FINGERPRINT LOOKUP
print("Step 2: Pre-calculating drug structures...")
smiles_dict = dict(zip(smiles_df['drug_name'], smiles_df['smiles']))
fp_lookup = {}

for name in pd.concat([df['Drug 1'], df['Drug 2']]).unique():
    smiles = smiles_dict.get(name)
    if not smiles or pd.isna(smiles):
        fp_lookup[name] = np.zeros(2048, dtype=np.int8)
        continue
    mol = Chem.MolFromSmiles(smiles)
    if mol:
        fp_lookup[name] = np.array(AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048), dtype=np.int8)
    else:
        fp_lookup[name] = np.zeros(2048, dtype=np.int8)

# 5. ASSEMBLE FEATURES
print("Step 3: Building feature matrix...")
X = np.zeros((len(df), 4096), dtype=np.int8)
for i, row in df.iterrows():
    X[i, :2048] = fp_lookup.get(row['Drug 1'], np.zeros(2048, dtype=np.int8))
    X[i, 2048:] = fp_lookup.get(row['Drug 2'], np.zeros(2048, dtype=np.int8))

# 6. SPLIT DATA
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 7. XGBOOST CONFIG (Auto-adjusts for Binary vs Multi-class)
print("Step 4: Training on GPU...")
params = {
    'tree_method': 'hist',
    'device': 'cuda', # Use your RTX 3050
    'n_estimators': 100,
    'learning_rate': 0.1,
    'max_depth': 6
}

# If only 2 classes, use binary; otherwise use multiclass
if num_unique_classes <= 2:
    params['objective'] = 'binary:logistic'
else:
    params['objective'] = 'multi:softprob'
    params['num_class'] = num_unique_classes

model = xgb.XGBClassifier(**params)
model.fit(X_train, y_train)

# 8. SAFE EVALUATION
y_pred = model.predict(X_test)
acc = accuracy_score(y_test, y_pred)

# 9. SAVE
joblib.dump(model, "astarva_model.pkl")
joblib.dump(le, "label_encoder.pkl")
print(f"Final Accuracy: {acc*100:.2f}%")