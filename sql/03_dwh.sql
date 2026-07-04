drop table if exists dwh.fact_vote_bureau;
drop table if exists dwh.fact_turnout_bureau;
drop table if exists dwh.dim_candidate;
drop table if exists dwh.dim_bureau;
drop table if exists dwh.dim_election;

create table dwh.dim_election (
  election_id serial primary key,
  id_election text not null unique,
  annee int,
  election_type text,
  tour int
);

create table dwh.dim_bureau (
  bureau_id serial primary key,
  id_brut_miom text not null unique,
  code_departement text,
  libelle_departement text,
  code_commune text,
  libelle_commune text,
  code_bv text,
  code_circonscription text,
  libelle_circonscription text,
  code_canton text,
  libelle_canton text
);

create table dwh.dim_candidate (
  candidate_id serial primary key,
  candidate_nk text not null unique,
  sexe text,
  nom text,
  prenom text,
  nuance text,
  liste text,
  libelle_abrege_liste text,
  libelle_etendu_liste text,
  nom_tete_liste text,
  binome text
);

create table dwh.fact_turnout_bureau (
  election_id int not null references dwh.dim_election(election_id),
  bureau_id int not null references dwh.dim_bureau(bureau_id),
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
  ratio_exprimes_votants double precision,
  primary key (election_id, bureau_id)
);

create table dwh.fact_vote_bureau (
  election_id int not null references dwh.dim_election(election_id),
  bureau_id int not null references dwh.dim_bureau(bureau_id),
  candidate_id int not null references dwh.dim_candidate(candidate_id),
  no_panneau int,
  voix int,
  ratio_voix_inscrits double precision,
  ratio_voix_exprimes double precision,
  primary key (election_id, bureau_id, candidate_id)
);
