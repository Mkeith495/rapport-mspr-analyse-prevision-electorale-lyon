drop materialized view if exists mart.ml_base_bureau;

create materialized view mart.ml_base_bureau as
select
  e.id_election,
  e.annee,
  e.election_type,
  e.tour,

  b.id_brut_miom,
  b.code_departement,
  b.code_commune,
  b.libelle_commune,
  b.code_bv,
  b.code_circonscription,
  b.libelle_circonscription,

  f.inscrits,
  f.votants,
  f.abstentions,
  f.blancs,
  f.nuls,
  f.exprimes,

  f.ratio_votants_inscrits as taux_participation,
  f.ratio_abstentions_inscrits as taux_abstention,
  f.ratio_exprimes_votants as taux_exprimes_sur_votants
from dwh.fact_turnout_bureau f
join dwh.dim_election e on e.election_id = f.election_id
join dwh.dim_bureau b on b.bureau_id = f.bureau_id;

create index if not exists idx_ml_base_bureau on mart.ml_base_bureau (id_election, id_brut_miom);
