import pandas as pd
# import numpy as np
# from rdkit import Chem
# from rdkit.Chem import AllChem
import os
import time 
import pubchempy as pcp

FILE_PATH = "ChronicAlly\db_drug_interactions.csv"
if not os.path.exists(FILE_PATH):
    print(f"Error: {FILE_PATH} not found in current directory.")
else:
    df = pd.read_csv(FILE_PATH)
    
    # 2. Extract unique drug names
    unique_drugs = pd.concat([df['Drug 1'], df['Drug 2']]).unique()
    print(f"Total unique drugs to map: {len(unique_drugs)}")

    # 3. Mapping loop
    smiles_data = []
    # We'll start with a test batch of 20 to make sure it works
    test_limit = 20 
    
    print(f"Starting lookup for first {test_limit} drugs...")
    
    for i, name in enumerate(unique_drugs[:test_limit]): 
        try:
            # Search PubChem by name
            compounds = pcp.get_compounds(name, 'name')
            if compounds:
                smiles = compounds[0].canonical_smiles
                smiles_data.append({"drug_name": name, "smiles": smiles})
                print(f"[{i+1}] Found: {name}")
            else:
                smiles_data.append({"drug_name": name, "smiles": None})
                print(f"[{i+1}] Not Found: {name}")
        except Exception as e:
            print(f"Error looking up {name}: {e}")
        
        time.sleep(0.2) # Avoid hitting API limits

    # 4. Save results
    mapping_df = pd.DataFrame(smiles_data)
    mapping_df.to_csv("smiles_mapping.csv", index=False)
    print("\nSuccess! 'smiles_mapping.csv' created.")
    