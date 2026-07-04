from __future__ import annotations
import os
import pandas as pd
import pyarrow.parquet as pq
from etl.config import Config

def inspect_parquet(path: str, sample_cols: list[str]) -> None:
    pf = pq.ParquetFile(path)
    print("\n===", os.path.basename(path), "===")
    print("Rows:", pf.metadata.num_rows)
    print("Columns:", pf.schema.names)

    # Sample (5 lignes)
    df_sample = pd.read_parquet(path, columns=[c for c in sample_cols if c in pf.schema.names]).head(5)
    print("\nSample (5 rows):")
    print(df_sample)

def main() -> None:
    cfg = Config()
    raw_dir = os.path.join(cfg.data_dir, "raw")

    p_general = os.path.join(raw_dir, "general_results.parquet")
    p_cand = os.path.join(raw_dir, "candidats_results.parquet")

    inspect_parquet(
        p_general,
        sample_cols=["id_election", "id_brut_miom", "code_departement", "code_commune", "code_bv", "inscrits", "votants", "abstentions"]
    )

    inspect_parquet(
        p_cand,
        sample_cols=["id_election", "id_brut_miom", "code_departement", "code_bv", "nom", "prenom", "nuance", "voix"]
    )

    # Liste des élections disponibles (colonne seule)
    df_ids = pd.read_parquet(p_general, columns=["id_election"])
    print("\nElections (id_election) distincts:", sorted(df_ids["id_election"].dropna().unique().tolist())[:30], "…")

if __name__ == "__main__":
    main()
