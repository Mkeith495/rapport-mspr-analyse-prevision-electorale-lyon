drop materialized view if exists mart.ml_features_bureau;

create materialized view mart.ml_features_bureau as
select
  b.*,
  w.winner_nuance,
  w.winner_ratio_exprimes,
  w.margin_ratio_exprimes,
  w.nb_candidates
from mart.ml_base_bureau b
left join mart.vote_winner_bureau w
  on w.id_election = b.id_election
 and w.id_brut_miom = b.id_brut_miom;

create index if not exists idx_ml_features_bureau on mart.ml_features_bureau (id_election, id_brut_miom);
