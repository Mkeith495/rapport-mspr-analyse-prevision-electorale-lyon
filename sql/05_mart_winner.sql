drop materialized view if exists mart.vote_winner_bureau;

create materialized view mart.vote_winner_bureau as
with ranked as (
  select
    f.election_id,
    f.bureau_id,
    f.candidate_id,
    f.voix,
    f.ratio_voix_exprimes,
    row_number() over (
      partition by f.election_id, f.bureau_id
      order by f.voix desc nulls last, f.candidate_id
    ) as rn
  from dwh.fact_vote_bureau f
),
agg as (
  select
    election_id,
    bureau_id,
    max(candidate_id) filter (where rn = 1) as winner_candidate_id,
    max(voix)        filter (where rn = 1) as winner_voix,
    max(ratio_voix_exprimes) filter (where rn = 1) as winner_ratio_exprimes,

    max(candidate_id) filter (where rn = 2) as runnerup_candidate_id,
    max(voix)        filter (where rn = 2) as runnerup_voix,
    max(ratio_voix_exprimes) filter (where rn = 2) as runnerup_ratio_exprimes,

    count(*) as nb_candidates
  from ranked
  group by 1,2
)
select
  e.id_election,
  b.id_brut_miom,
  b.libelle_commune,
  b.code_bv,

  a.nb_candidates,

  a.winner_candidate_id,
  cw.nom    as winner_nom,
  cw.prenom as winner_prenom,
  cw.nuance as winner_nuance,
  a.winner_voix,
  a.winner_ratio_exprimes,

  a.runnerup_candidate_id,
  cr.nom    as runnerup_nom,
  cr.prenom as runnerup_prenom,
  cr.nuance as runnerup_nuance,
  a.runnerup_voix,
  a.runnerup_ratio_exprimes,

  (a.winner_voix - a.runnerup_voix) as margin_voix,
  (a.winner_ratio_exprimes - a.runnerup_ratio_exprimes) as margin_ratio_exprimes

from agg a
join dwh.dim_election e on e.election_id = a.election_id
join dwh.dim_bureau b   on b.bureau_id   = a.bureau_id
left join dwh.dim_candidate cw on cw.candidate_id = a.winner_candidate_id
left join dwh.dim_candidate cr on cr.candidate_id = a.runnerup_candidate_id;

create index if not exists idx_vote_winner_bureau on mart.vote_winner_bureau (id_election, id_brut_miom);
