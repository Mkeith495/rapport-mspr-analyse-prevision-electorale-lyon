from __future__ import annotations
import re
import pandas as pd
import pyarrow.dataset as ds

def read_parquet_dep(path: str, dep: str) -> pd.DataFrame:
    dep = str(dep).zfill(2)
    dataset = ds.dataset(path, format="parquet")
    table = dataset.to_table(filter=(ds.field("code_departement") == dep))
    return table.to_pandas()

def filter_lyon_general(df: pd.DataFrame, commune_regex: str = r"^Lyon") -> pd.DataFrame:
    # filtre département déjà fait; ici on filtre les communes "Lyon ..."
    return df[df["libelle_commune"].astype("string").str.contains(commune_regex, case=False, na=False, regex=True)].copy()

def make_candidate_nk(df: pd.DataFrame) -> pd.Series:
    def norm(x):
        if pd.isna(x):
            return ""
        return str(x).strip().lower()

    return (
        df.apply(lambda r: "|".join([
            norm(r.get("nom")),
            norm(r.get("prenom")),
            norm(r.get("sexe")),
            norm(r.get("nuance")),
            norm(r.get("liste")),
            norm(r.get("nom_tete_liste")),
            norm(r.get("binome")),
        ]), axis=1)
    )

def transform_general(path_general: str, dep: str = "69", commune_regex: str = r"^Lyon", election_whitelist: list[str] | None = None) -> pd.DataFrame:
    df = read_parquet_dep(path_general, dep)
    df = filter_lyon_general(df, commune_regex=commune_regex)
    if election_whitelist:
        df = df[df["id_election"].isin(election_whitelist)].copy()
    # normaliser codes en string (important pour joins)
    df["code_departement"] = df["code_departement"].astype("string").str.zfill(2)
    df["code_commune"] = df["code_commune"].astype("string").str.zfill(5)
    df["code_bv"] = df["code_bv"].astype("string").str.zfill(4)
    return df

def transform_candidats(path_cand: str, lyon_bureaux: set[str], dep: str = "69", election_whitelist: list[str] | None = None) -> pd.DataFrame:
    df = read_parquet_dep(path_cand, dep)
    if election_whitelist:
        df = df[df["id_election"].isin(election_whitelist)].copy()
    # on garde uniquement les bureaux réellement Lyon (issus du general)
    df = df[df["id_brut_miom"].isin(lyon_bureaux)].copy()

    df["code_departement"] = df["code_departement"].astype("string").str.zfill(2)
    df["code_commune"] = df["code_commune"].astype("string").str.zfill(5)
    df["code_bv"] = df["code_bv"].astype("string").str.zfill(4)

    df["candidate_nk"] = make_candidate_nk(df)
    return df

def transform_delinquance(path_delinq: str, code_communes: set[str]) -> pd.DataFrame:
    import pyarrow.dataset as ds

    dataset = ds.dataset(path_delinq, format="parquet")
    expr = ds.field("CODGEO_2025").isin(list(code_communes))
    table = dataset.to_table(filter=expr)
    df = table.to_pandas()

    df = df.rename(columns={"CODGEO_2025": "code_commune"})
    df["code_commune"] = df["code_commune"].astype("string").str.zfill(5)
    df["annee"] = df["annee"].astype(int)
    return df

def parse_periode_to_year_q(periode: str) -> tuple[int, int]:
    m = re.match(r"^(\d{4})-T(\d)$", str(periode).strip())
    if not m:
        raise ValueError(f"Periode invalide: {periode}")
    return int(m.group(1)), int(m.group(2))

def iter_transform_demandeurs_csv(path_csv: str, code_communes: set[str], dep: str = "69", chunksize: int = 400_000):
    dep = str(dep).zfill(2)

    usecols = [
        "Date", "Code région", "Région", "Code département", "Département",
        "Code commune", "Commune", "Type de données", "Catégorie", "Sexe",
        "Tranche d'âge", "Nombre de demandeurs d'emploi"
    ]

    for chunk in pd.read_csv(path_csv, usecols=usecols, dtype=str, chunksize=chunksize, sep=";"):
        chunk = chunk.rename(columns={
            "Date": "periode",
            "Code région": "code_region",
            "Région": "region",
            "Code département": "code_departement",
            "Département": "departement",
            "Code commune": "code_commune",
            "Commune": "commune",
            "Type de données": "type_donnees",
            "Catégorie": "categorie",
            "Sexe": "sexe",
            "Tranche d'âge": "tranche_age",
            "Nombre de demandeurs d'emploi": "nb_demandeurs",
        })

        chunk["code_departement"] = chunk["code_departement"].astype("string").str.zfill(2)
        chunk["code_commune"] = chunk["code_commune"].astype("string").str.zfill(5)

        # filtre dep + lyon via codes
        chunk = chunk[chunk["code_departement"] == dep]
        chunk = chunk[chunk["code_commune"].isin(code_communes)]

        # filtre segment (POC)
        chunk = chunk[chunk["type_donnees"].eq("Brutes")]
        chunk = chunk[chunk["categorie"].eq("ABC")]
        chunk = chunk[chunk["sexe"].eq("Total")]
        chunk = chunk[chunk["tranche_age"].isin(["Total", "Moins de 25 ans", "50 ans et plus"])]

        if chunk.empty:
            continue

        # parse periode -> annee/trimestre
        yq = chunk["periode"].map(parse_periode_to_year_q)
        chunk["annee"] = yq.map(lambda t: t[0])
        chunk["trimestre"] = yq.map(lambda t: t[1])

        chunk["nb_demandeurs"] = pd.to_numeric(chunk["nb_demandeurs"], errors="coerce").fillna(0).astype("int64")

        yield chunk