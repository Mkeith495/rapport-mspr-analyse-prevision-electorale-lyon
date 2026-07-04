create table if not exists dwh.dim_chomage_segment (
  segment_id serial primary key,
  categorie text not null,
  sexe text not null,
  tranche_age text not null,
  unique (categorie, sexe, tranche_age)
);

create table if not exists dwh.fact_demandeurs_commune_quarter (
  code_commune text not null,
  annee int not null,
  trimestre int not null,
  segment_id int not null references dwh.dim_chomage_segment(segment_id),
  nb_demandeurs int,
  primary key (code_commune, annee, trimestre, segment_id)
);

create index if not exists idx_fact_demandeurs_commune_quarter
on dwh.fact_demandeurs_commune_quarter (code_commune, annee, trimestre);
