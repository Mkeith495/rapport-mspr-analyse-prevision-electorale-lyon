create table if not exists stg.delinquance (
  code_commune text not null,
  annee int not null,
  indicateur text not null,
  unite_de_compte text,
  nombre int,
  taux_pour_mille double precision,
  est_diffuse text,
  insee_pop int,
  insee_pop_millesime int,
  insee_log int,
  insee_log_millesime int,
  complement_info_nombre double precision,
  complement_info_taux double precision
);

create index if not exists idx_stg_delinquance_key
on stg.delinquance (code_commune, annee, indicateur);
