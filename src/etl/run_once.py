from __future__ import annotations
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

from etl.transform import iter_transform_demandeurs_csv, transform_delinquance, transform_general, transform_candidats
from etl.load import load_stg_demandeurs, truncate_stg, load_stg, build_dwh

load_dotenv()

PG_URL = f"postgresql+psycopg2://{os.getenv('POSTGRES_USER','postgres')}:{os.getenv('POSTGRES_PASSWORD','postgres')}@{os.getenv('POSTGRES_HOST','localhost')}:{os.getenv('POSTGRES_PORT','5432')}/{os.getenv('POSTGRES_DB','lyon_dwh')}"
DATA_DIR = os.getenv("DATA_DIR", "./data")

def main():
    engine = create_engine(PG_URL, future=True)

    path_general = os.path.join(DATA_DIR, "raw", "general_results.parquet")
    path_cand = os.path.join(DATA_DIR, "raw", "candidats_results.parquet")
    path_delinq = os.path.join(DATA_DIR, "raw", "delinquance.parquet")
    path_chomage = os.path.join(DATA_DIR, "raw", "inscrits_chomage.csv")

    df_general = transform_general(path_general, dep="69", commune_regex=r"^Lyon")
    lyon_bureaux = set(df_general["id_brut_miom"].unique().tolist())
    df_cand = transform_candidats(path_cand, lyon_bureaux=lyon_bureaux, dep="69")
    
    lyon_communes = set(df_general["code_commune"].unique().tolist())
    df_delinq = transform_delinquance(path_delinq, code_communes=lyon_communes)

    truncate_stg(engine)
    load_stg(engine, df_general, df_cand, df_delinq) 

    total = 0
    for df_chunk in iter_transform_demandeurs_csv(path_chomage, code_communes=lyon_communes, dep="69"):
        load_stg_demandeurs(engine, df_chunk)
        total += len(df_chunk)

    print("Chomage rows loaded (filtered Lyon):", total)
    print("Lyon general rows:", len(df_general))
    print("Lyon candidats rows:", len(df_cand))
    print("Delinquance rows:", len(df_delinq))

    build_dwh(engine)

    print("OK: stg + dwh remplis")

if __name__ == "__main__":
    main()
