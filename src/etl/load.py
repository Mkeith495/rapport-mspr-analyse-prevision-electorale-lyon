from __future__ import annotations
import pandas as pd
from sqlalchemy import create_engine, text

def truncate_stg(engine):
    with engine.begin() as conn:
        conn.execute(text("truncate table stg.general_results;"))
        conn.execute(text("truncate table stg.candidats_results;"))
        conn.execute(text("truncate table stg.delinquance;"))
        conn.execute(text("truncate table stg.demandeurs_emploi;"))

def load_stg(engine, df_general: pd.DataFrame, df_cand: pd.DataFrame, df_delinq=None):
    df_general.to_sql("general_results", engine, schema="stg", if_exists="append", index=False, method="multi", chunksize=5000)
    df_cand.to_sql("candidats_results", engine, schema="stg", if_exists="append", index=False, method="multi", chunksize=5000)
    if df_delinq is not None and len(df_delinq) > 0:
      df_delinq.to_sql("delinquance", engine, schema="stg", if_exists="append", index=False)

def load_stg_delinquance(engine, df):
    df.to_sql("delinquance", engine, schema="stg", if_exists="append",
              index=False, method="multi", chunksize=5000)

def load_stg_demandeurs(engine, df: pd.DataFrame):
    df.to_sql(
        "demandeurs_emploi",
        engine,
        schema="stg",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=5000
    )

def build_dwh(engine):
    sql = """
    -- 1) dim_election
    insert into dwh.dim_election (id_election, annee, election_type, tour)
    select distinct
      id_election,
      nullif(substring(id_election from 1 for 4),'')::int as annee,
      split_part(id_election, '_', 2) as election_type,
      nullif(replace(split_part(id_election, '_', 3), 't', ''), '')::int as tour
    from stg.general_results
    on conflict (id_election) do nothing;

    -- 2) dim_bureau (une ligne par id_brut_miom)
    insert into dwh.dim_bureau (
      id_brut_miom, code_departement, libelle_departement,
      code_commune, libelle_commune, code_bv,
      code_circonscription, libelle_circonscription,
      code_canton, libelle_canton
    )
    select distinct on (id_brut_miom)
      id_brut_miom, code_departement, libelle_departement,
      code_commune, libelle_commune, code_bv,
      code_circonscription, libelle_circonscription,
      code_canton, libelle_canton
    from stg.general_results
    order by id_brut_miom
    on conflict (id_brut_miom) do nothing;

    -- 3) dim_candidate (une ligne par candidate_nk)
    insert into dwh.dim_candidate (
      candidate_nk, sexe, nom, prenom, nuance, liste,
      libelle_abrege_liste, libelle_etendu_liste, nom_tete_liste, binome
    )
    select distinct on (candidate_nk)
      candidate_nk, sexe, nom, prenom, nuance, liste,
      libelle_abrege_liste, libelle_etendu_liste, nom_tete_liste, binome
    from stg.candidats_results
    where candidate_nk is not null and candidate_nk <> ''
    order by candidate_nk
    on conflict (candidate_nk) do nothing;

    -- 4) facts turnout (DEDUP par id_election + id_brut_miom)
    with g_dedup as (
      select
        id_election,
        id_brut_miom,
        max(inscrits) as inscrits,
        max(abstentions) as abstentions,
        max(votants) as votants,
        max(blancs) as blancs,
        max(nuls) as nuls,
        max(exprimes) as exprimes,
        max(ratio_abstentions_inscrits) as ratio_abstentions_inscrits,
        max(ratio_votants_inscrits) as ratio_votants_inscrits,
        max(ratio_blancs_inscrits) as ratio_blancs_inscrits,
        max(ratio_blancs_votants) as ratio_blancs_votants,
        max(ratio_nuls_inscrits) as ratio_nuls_inscrits,
        max(ratio_nuls_votants) as ratio_nuls_votants,
        max(ratio_exprimes_inscrits) as ratio_exprimes_inscrits,
        max(ratio_exprimes_votants) as ratio_exprimes_votants
      from stg.general_results
      group by 1,2
    )
    insert into dwh.fact_turnout_bureau (
      election_id, bureau_id,
      inscrits, abstentions, votants, blancs, nuls, exprimes,
      ratio_abstentions_inscrits, ratio_votants_inscrits,
      ratio_blancs_inscrits, ratio_blancs_votants,
      ratio_nuls_inscrits, ratio_nuls_votants,
      ratio_exprimes_inscrits, ratio_exprimes_votants
    )
    select
      e.election_id,
      b.bureau_id,
      g.inscrits, g.abstentions, g.votants, g.blancs, g.nuls, g.exprimes,
      g.ratio_abstentions_inscrits, g.ratio_votants_inscrits,
      g.ratio_blancs_inscrits, g.ratio_blancs_votants,
      g.ratio_nuls_inscrits, g.ratio_nuls_votants,
      g.ratio_exprimes_inscrits, g.ratio_exprimes_votants
    from g_dedup g
    join dwh.dim_election e on e.id_election = g.id_election
    join dwh.dim_bureau b on b.id_brut_miom = g.id_brut_miom
    on conflict (election_id, bureau_id) do update set
      inscrits = excluded.inscrits,
      abstentions = excluded.abstentions,
      votants = excluded.votants,
      blancs = excluded.blancs,
      nuls = excluded.nuls,
      exprimes = excluded.exprimes,
      ratio_abstentions_inscrits = excluded.ratio_abstentions_inscrits,
      ratio_votants_inscrits = excluded.ratio_votants_inscrits,
      ratio_blancs_inscrits = excluded.ratio_blancs_inscrits,
      ratio_blancs_votants = excluded.ratio_blancs_votants,
      ratio_nuls_inscrits = excluded.ratio_nuls_inscrits,
      ratio_nuls_votants = excluded.ratio_nuls_votants,
      ratio_exprimes_inscrits = excluded.ratio_exprimes_inscrits,
      ratio_exprimes_votants = excluded.ratio_exprimes_votants;

    -- 5) facts vote (DEDUP par id_election + id_brut_miom + candidate_nk)
    with r_dedup as (
      select
        id_election,
        id_brut_miom,
        candidate_nk,
        max(no_panneau) as no_panneau,
        sum(coalesce(voix,0)) as voix,
        max(ratio_voix_inscrits) as ratio_voix_inscrits,
        max(ratio_voix_exprimes) as ratio_voix_exprimes
      from stg.candidats_results
      where candidate_nk is not null and candidate_nk <> ''
      group by 1,2,3
    )
    insert into dwh.fact_vote_bureau (
      election_id, bureau_id, candidate_id,
      no_panneau, voix, ratio_voix_inscrits, ratio_voix_exprimes
    )
    select
      e.election_id,
      b.bureau_id,
      c.candidate_id,
      r.no_panneau,
      r.voix,
      r.ratio_voix_inscrits,
      r.ratio_voix_exprimes
    from r_dedup r
    join dwh.dim_election e on e.id_election = r.id_election
    join dwh.dim_bureau b on b.id_brut_miom = r.id_brut_miom
    join dwh.dim_candidate c on c.candidate_nk = r.candidate_nk
    on conflict (election_id, bureau_id, candidate_id) do update set
      no_panneau = excluded.no_panneau,
      voix = excluded.voix,
      ratio_voix_inscrits = excluded.ratio_voix_inscrits,
      ratio_voix_exprimes = excluded.ratio_voix_exprimes;
    
    -- dim indicateur
    insert into dwh.dim_delinquance_indicateur (indicateur, unite_de_compte)
    select indicateur, max(unite_de_compte) as unite_de_compte
    from stg.delinquance
    group by indicateur
    on conflict (indicateur) do update set unite_de_compte = excluded.unite_de_compte;

    -- fact
    insert into dwh.fact_delinquance_commune_year (
      indicateur_id, code_commune, annee,
      nombre, taux_pour_mille, est_diffuse,
      insee_pop, insee_pop_millesime, insee_log, insee_log_millesime,
      complement_info_nombre, complement_info_taux
    )
    select
      i.indicateur_id,
      s.code_commune,
      s.annee,
      max(s.nombre) as nombre,
      max(s.taux_pour_mille) as taux_pour_mille,
      max(s.est_diffuse) as est_diffuse,
      max(s.insee_pop) as insee_pop,
      max(s.insee_pop_millesime) as insee_pop_millesime,
      max(s.insee_log) as insee_log,
      max(s.insee_log_millesime) as insee_log_millesime,
      max(s.complement_info_nombre) as complement_info_nombre,
      max(s.complement_info_taux) as complement_info_taux
    from stg.delinquance s
    join dwh.dim_delinquance_indicateur i on i.indicateur = s.indicateur
    group by i.indicateur_id, s.code_commune, s.annee
    on conflict (indicateur_id, code_commune, annee) do update set
      nombre = excluded.nombre,
      taux_pour_mille = excluded.taux_pour_mille,
      est_diffuse = excluded.est_diffuse,
      insee_pop = excluded.insee_pop,
      insee_pop_millesime = excluded.insee_pop_millesime,
      insee_log = excluded.insee_log,
      insee_log_millesime = excluded.insee_log_millesime,
      complement_info_nombre = excluded.complement_info_nombre,
      complement_info_taux = excluded.complement_info_taux;

    insert into dwh.dim_chomage_segment (categorie, sexe, tranche_age)
    select distinct categorie, sexe, tranche_age
    from stg.demandeurs_emploi
    on conflict (categorie, sexe, tranche_age) do nothing;

    insert into dwh.fact_demandeurs_commune_quarter (code_commune, annee, trimestre, segment_id, nb_demandeurs)
    select
      s.code_commune,
      s.annee,
      s.trimestre,
      seg.segment_id,
      max(s.nb_demandeurs) as nb_demandeurs
    from stg.demandeurs_emploi s
    join dwh.dim_chomage_segment seg
      on seg.categorie = s.categorie and seg.sexe = s.sexe and seg.tranche_age = s.tranche_age
    group by 1,2,3,4
    on conflict (code_commune, annee, trimestre, segment_id) do update set
      nb_demandeurs = excluded.nb_demandeurs;

    """
    with engine.begin() as conn:
        conn.execute(text(sql))
