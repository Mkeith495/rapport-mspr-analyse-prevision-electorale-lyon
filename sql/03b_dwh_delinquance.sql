create table if not exists dwh.dim_delinquance_indicateur (
  indicateur_id serial primary key,
  indicateur text not null unique,
  unite_de_compte text
);

create table if not exists dwh.fact_delinquance_commune_year (
  indicateur_id int not null references dwh.dim_delinquance_indicateur(indicateur_id),
  code_commune text not null,
  annee int not null,

  nombre int,
  taux_pour_mille double precision,
  est_diffuse text,

  insee_pop int,
  insee_pop_millesime int,
  insee_log int,
  insee_log_millesime int,

  complement_info_nombre double precision,
  complement_info_taux double precision,

  primary key (indicateur_id, code_commune, annee)
);

create index if not exists idx_fact_delinquance_commune_year
on dwh.fact_delinquance_commune_year (code_commune, annee);
