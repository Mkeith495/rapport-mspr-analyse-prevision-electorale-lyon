create table if not exists stg.demandeurs_emploi (
  periode text not null,
  annee int not null,
  trimestre int not null,

  code_region text,
  region text,
  code_departement text,
  departement text,

  code_commune text not null,
  commune text,

  type_donnees text,
  categorie text,
  sexe text,
  tranche_age text,

  nb_demandeurs int
);

create index if not exists idx_stg_demandeurs_key
on stg.demandeurs_emploi (code_commune, annee, trimestre, categorie, sexe, tranche_age);
