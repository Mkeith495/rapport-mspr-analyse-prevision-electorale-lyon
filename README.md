# Rapport MSPR — Analyse et prévision électorale sur Lyon

Projet MSPR solo autour de l'analyse électorale lyonnaise. Le projet construit une chaîne data complète permettant de charger des données publiques, de les structurer dans PostgreSQL, de créer des vues analytiques, puis de produire des visualisations et un modèle de machine learning pour prédire la nuance politique gagnante par bureau de vote.

## Objectifs

- Structurer des données électorales, de chômage et de délinquance sur Lyon.
- Construire un Data Warehouse PostgreSQL en couches `stg`, `dwh` et `mart`.
- Produire une table finale `mart.ml_features_bureau_final` exploitable en analyse.
- Générer des visualisations Python sur les corrélations, les modèles et les clusters.
- Comparer plusieurs modèles supervisés pour prédire `winner_nuance`.

## Architecture du projet

```text
.
├── sql/                 # Scripts SQL de création des schémas, tables et vues matérialisées
├── src/
│   ├── etl/             # Pipeline ETL Python
│   └── ml/              # Pipeline machine learning et visualisations
├── data/                # Données locales non versionnées
├── requirements.txt     # Dépendances Python
├── docker-compose.yml   # Services techniques du projet
└── .env.example         # Exemple de configuration locale
```

## Prérequis

- Python 3.11 ou version compatible récente
- PostgreSQL accessible localement ou via Docker
- Git
- Données brutes attendues dans `data/raw/`

## Données attendues

Les données brutes sont volumineuses et ne sont pas incluses dans le dépôt Git. Pour exécuter l'ETL, placer les fichiers suivants dans `data/raw/` :

```text
data/raw/general_results.parquet
data/raw/candidats_results.parquet
data/raw/delinquance.parquet
data/raw/inscrits_chomage.csv
```

## Configuration

Créer un fichier `.env` à partir de `.env.example` :

```bash
cp .env.example .env
```

Exemple de configuration :

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=lyon_dwh
DATA_DIR=./data
```

## Installation Python

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

## Initialisation SQL

Les scripts SQL doivent être exécutés dans l'ordre numérique :

```text
sql/01_init.sql
sql/02_stg.sql
sql/02b_stg_delinquance.sql
sql/02c_stg_chomage.sql
sql/03_dwh.sql
sql/03b_dwh_delinquance.sql
sql/03c_dwh_chomage.sql
sql/04_mart.sql
sql/05_mart_winner.sql
sql/06_mart_features.sql
sql/08_mart_delinquance.sql
sql/09_mart_chomage.sql
```

## Lancement de l'ETL

Depuis la racine du projet :

```bash
PYTHONPATH=src python src/etl/run_once.py
```

Le pipeline charge les fichiers sources, filtre le périmètre lyonnais, alimente les tables `stg`, puis reconstruit les dimensions, les faits et les vues analytiques.

## Lancement du module ML

Après exécution de l'ETL et création de `mart.ml_features_bureau_final` :

```bash
PYTHONPATH=src python src/ml/predict.py
```

Les graphiques sont générés dans :

```text
src/ml/outputs/
```

## Sorties ML principales

- `01_correlation_heatmap.png`
- `02_correlation_spearman.png`
- `03_scatter_chomage_participation.png`
- `04_scatter_cambriolages_participation.png`
- `05_model_comparison.png`
- `06_feature_importances.png`
- `07_kmeans_elbow.png`
- `08_kmeans_pca.png`
- `09_cluster_profiles.png`
- `10_cluster_nuances.png`

## Résultats principaux du POC

- Vue finale utilisée : `mart.ml_features_bureau_final`
- Cible ML : `winner_nuance`
- Modèles comparés : Random Forest, Gradient Boosting, régression logistique
- Meilleur modèle : Random Forest
- Accuracy moyenne en validation croisée : environ 73 %
- Accuracy sur jeu de test : environ 72 %

## Position sur Metabase et Traefik

Metabase et Traefik font partie de l'architecture projet, mais leur rôle est distinct du pipeline analytique.

- Python porte les visualisations analytiques du POC.
- PostgreSQL porte le stockage, le Data Warehouse et les vues `mart`.
- Metabase correspond à la couche de restitution BI cible.
- Traefik correspond à la couche d'exposition des services en contexte d'industrialisation.

## Limites

Le dépôt contient le code, les scripts SQL et les visualisations générées. Les données brutes ne sont pas versionnées dans Git pour éviter d'alourdir le dépôt. Une personne souhaitant relancer l'intégralité du pipeline doit disposer des fichiers sources attendus dans `data/raw/` et d'une base PostgreSQL correctement configurée.
