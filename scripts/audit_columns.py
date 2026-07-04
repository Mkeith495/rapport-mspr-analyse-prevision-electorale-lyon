import pandas as pd
import os

# Liste des fichiers à tester (Modifie les noms si tes fichiers sont différents)
DATA_DIR = r"D:\MSPR_SOLO\data" # Ton chemin vers les données

files_to_check = [
    ("GENERAL", "general_results.parquet"),
    ("CANDIDATS", "candidats_results.parquet"),
    ("DELINQUANCE", "delinquance.parquet"),
    ("CHOMAGE", "inscrits_chomage.csv")
]

def audit():
    print(f"🔍 Début de l'audit dans : {DATA_DIR}\n" + "="*50)
    
    for label, filename in files_to_check:
        path = os.path.join(DATA_DIR, filename)
        
        if not os.path.exists(path):
            print(f"❌ {label} : Fichier '{filename}' introuvable.")
            continue
            
        try:
            # Lecture des 5 premières lignes seulement pour la rapidité
            if filename.endswith('.csv'):
                df = pd.read_csv(path, nrows=5)
            else:
                df = pd.read_parquet(path)
                df = df.head(5)
            
            print(f"\n✅ {label} ({filename})")
            print(f"--- Colonnes détectées ({len(df.columns)}) :")
            for i, col in enumerate(df.columns):
                print(f"  {i+1}. {col}")
            
            # Petit aperçu de la première ligne pour voir le format des données
            print(f"--- Exemple de données (Ligne 1) :")
            print(f"  {df.iloc[0].to_dict()}")
            
        except Exception as e:
            print(f"❌ {label} : Erreur lors de la lecture -> {e}")
        
    print("\n" + "="*50 + "\n✅ Audit terminé.")

if __name__ == "__main__":
    audit()