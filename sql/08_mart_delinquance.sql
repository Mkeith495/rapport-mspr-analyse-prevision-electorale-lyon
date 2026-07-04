drop materialized view if exists mart.delinquance_commune_year;

create materialized view mart.delinquance_commune_year as
select
  f.code_commune,
  f.annee,

  max(f.taux_pour_mille) filter (where i.indicateur = 'Violences sexuelles') as delinq_violences_sexuelles_taux,
  max(f.nombre)         filter (where i.indicateur = 'Violences sexuelles') as delinq_violences_sexuelles_nombre,

  max(f.taux_pour_mille) filter (where i.indicateur = 'Cambriolages de logement') as delinq_cambriolages_taux,
  max(f.nombre)         filter (where i.indicateur = 'Cambriolages de logement') as delinq_cambriolages_nombre,

  max(f.taux_pour_mille) filter (where i.indicateur = 'Vols de véhicule') as delinq_vols_vehicule_taux,
  max(f.nombre)         filter (where i.indicateur = 'Vols de véhicule') as delinq_vols_vehicule_nombre,

  max(f.taux_pour_mille) filter (where i.indicateur = 'Usage de stupéfiants') as delinq_stupefiants_taux,
  max(f.nombre)         filter (where i.indicateur = 'Usage de stupéfiants') as delinq_stupefiants_nombre

from dwh.fact_delinquance_commune_year f
join dwh.dim_delinquance_indicateur i on i.indicateur_id = f.indicateur_id
group by 1,2;

create index if not exists idx_mart_delinquance_commune_year
on mart.delinquance_commune_year (code_commune, annee);


drop materialized view if exists mart.ml_features_bureau_enriched;

create materialized view mart.ml_features_bureau_enriched as
select
  m.*,
  d.delinq_violences_sexuelles_taux,
  d.delinq_violences_sexuelles_nombre,
  d.delinq_cambriolages_taux,
  d.delinq_cambriolages_nombre,
  d.delinq_vols_vehicule_taux,
  d.delinq_vols_vehicule_nombre,
  d.delinq_stupefiants_taux,
  d.delinq_stupefiants_nombre
from mart.ml_features_bureau m
left join mart.delinquance_commune_year d
  on d.code_commune = m.code_commune
 and d.annee = m.annee - 1;

create index if not exists idx_ml_features_bureau_enriched
on mart.ml_features_bureau_enriched (id_election, id_brut_miom);
