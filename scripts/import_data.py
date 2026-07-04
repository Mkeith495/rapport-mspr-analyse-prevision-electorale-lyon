import os
import pandas as pd
from sqlalchemy import create_engine

# 1. CONNEXION
engine = create_engine("postgresql://admin:password123@localhost:5432/electio_db")

# 2. CHEMINS
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

def run():
    print("🚀 Lancement de l'importation chirurgicale (Périmètre Lyon)...")

    try:
        # --- A. GENERAL RESULTS ---
        print("📦 Import : General Results...")
        df_gen = pd.read_parquet(os.path.join(DATA_DIR, "general_results.parquet"))
        # Filtre Lyon (Département 69 + Libellé Lyon)
        df_gen = df_gen[df_gen["code_departement"].astype(str) == "69"].copy()
        df_gen = df_gen[df_gen["libelle_commune"].str.contains(r"^Lyon", case=False, na=False)].copy()
        df_gen["code_commune"] = df_gen["code_commune"].astype(str).str.zfill(5)
        
        lyon_codes = df_gen["code_commune"].unique().tolist()
        lyon_bureaux = df_gen["id_brut_miom"].unique().tolist()

        # --- B. CANDIDATS ---
        print("📦 Import : Candidats...")
        df_cand = pd.read_parquet(os.path.join(DATA_DIR, "candidats_results.parquet"))
        df_cand = df_cand[df_cand["id_brut_miom"].isin(lyon_bureaux)].copy()

        # --- C. DELINQUANCE (Correction CODGEO_2025) ---
        print("📦 Import : Délinquance...")
        df_del = pd.read_parquet(os.path.join(DATA_DIR, "delinquance.parquet"))
        # On utilise CODGEO_2025 comme identifié par l'audit
        df_del["code_commune"] = df_del["CODGEO_2025"].astype(str).str.zfill(5)
        df_del = df_del[df_del["code_commune"].isin(lyon_codes)].copy()

        # --- D. CHOMAGE (Correction Séparateur ;) ---
        print("📦 Import : Chômage...")
        # On précise sep=';' pour que Pandas lise bien les colonnes
        df_cho = pd.read_csv(os.path.join(DATA_DIR, "inscrits_chomage.csv"), sep=';')
        df_cho["code_commune"] = df_cho["Code commune"].astype(str).str.zfill(5)
        # Filtres standards
        df_cho = df_cho[
            (df_cho["code_commune"].isin(lyon_codes)) & 
            (df_cho["Type de données"] == "Brutes") & 
            (df_cho["Catégorie"] == "ABC")
        ].copy()

        # 3. ENVOI EN BASE
        print("📥 Injection dans PostgreSQL...")
        df_gen.to_sql("stg_general_results", engine, if_exists="replace", index=False)
        df_cand.to_sql("stg_candidats_results", engine, if_exists="replace", index=False)
        df_del.to_sql("stg_delinquance", engine, if_exists="replace", index=False)
        df_cho.to_sql("stg_chomage", engine, if_exists="replace", index=False)

        print(f"\n✨ IMPORT REUSSI !")
        print(f"📊 Stats Lyon : {len(df_gen)} bureaux de vote, {len(df_del)} faits de délinquance.")

    except Exception as e:
        print(f"❌ ERREUR : {e}")

if __name__ == "__main__":
    run()