import os

# Chemins absolus pour éviter les erreurs de dossier
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Connexion Base de données
DB_URL = "postgresql://admin:password123@localhost:5432/electio_db"

# Noms exacts des fichiers (Vérifie bien qu'ils sont dans /data)
FILES = {
    "general": os.path.join(DATA_DIR, "general_results.parquet"),
    "candidats": os.path.join(DATA_DIR, "candidats_results.parquet"),
    "delinquance": os.path.join(DATA_DIR, "delinquance.parquet"),
    "chomage": os.path.join(DATA_DIR, "inscrits_chomage.csv")
}