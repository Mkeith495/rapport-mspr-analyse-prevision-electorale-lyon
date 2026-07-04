create schema if not exists raw;
create schema if not exists stg;
create schema if not exists dwh;
create schema if not exists mart;

create table if not exists raw.etl_run (
  run_id uuid primary key,
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  status text not null,
  note text
);
