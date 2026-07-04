drop materialized view if exists mart.chomage_commune_year;

create materialized view mart.chomage_commune_year as
select
  f.code_commune,
  f.annee,

  max(f.nb_demandeurs) filter (where seg.tranche_age = 'Total') as chomage_abc_total,
  max(f.nb_demandeurs) filter (where seg.tranche_age = 'Moins de 25 ans') as chomage_abc_moins25,
  max(f.nb_demandeurs) filter (where seg.tranche_age = '50 ans et plus') as chomage_abc_50plus
from dwh.fact_demandeurs_commune_quarter f
join dwh.dim_chomage_segment seg on seg.segment_id = f.segment_id
where f.trimestre = 4
  and seg.categorie = 'ABC'
  and seg.sexe = 'Total'
group by 1,2;

create index if not exists idx_mart_chomage_commune_year
on mart.chomage_commune_year (code_commune, annee);


drop materialized view if exists mart.ml_features_bureau_final;

create materialized view mart.ml_features_bureau_final as
select
  m.*,
  c.chomage_abc_total,
  c.chomage_abc_moins25,
  c.chomage_abc_50plus
from mart.ml_features_bureau_enriched m
left join mart.chomage_commune_year c
  on c.code_commune = m.code_commune
 and c.annee = m.annee - 1;

create index if not exists idx_ml_features_bureau_final
on mart.ml_features_bureau_final (id_election, id_brut_miom);
