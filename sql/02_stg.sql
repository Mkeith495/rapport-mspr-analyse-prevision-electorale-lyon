drop table if exists stg.general_results;
create table stg.general_results (
  id_election text not null,
  id_brut_miom text not null,
  code_departement text,
  libelle_departement text,
  code_canton text,
  libelle_canton text,
  code_commune text,
  libelle_commune text,
  code_circonscription text,
  libelle_circonscription text,
  code_bv text,
  inscrits int,
  abstentions int,
  votants int,
  blancs int,
  nuls int,
  exprimes int,
  ratio_abstentions_inscrits double precision,
  ratio_votants_inscrits double precision,
  ratio_blancs_inscrits double precision,
  ratio_blancs_votants double precision,
  ratio_nuls_inscrits double precision,
  ratio_nuls_votants double precision,
  ratio_exprimes_inscrits double precision,
  ratio_exprimes_votants double precision
);

drop table if exists stg.candidats_results;
create table stg.candidats_results (
  id_election text not null,
  id_brut_miom text not null,
  code_departement text,
  code_commune text,
  code_bv text,
  no_panneau int,
  voix int,
  ratio_voix_inscrits double precision,
  ratio_voix_exprimes double precision,
  nuance text,
  sexe text,
  nom text,
  prenom text,
  liste text,
  libelle_abrege_liste text,
  libelle_etendu_liste text,
  nom_tete_liste text,
  binome text,
  candidate_nk text
);

create index if not exists idx_stg_gen_join on stg.general_results (id_election, id_brut_miom);
create index if not exists idx_stg_gen_geo on stg.general_results (code_departement, libelle_commune);
create index if not exists idx_stg_cand_join on stg.candidats_results (id_election, id_brut_miom);
