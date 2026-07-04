"""
ML Pipeline - Corrélations socio-économiques / comportements de vote
Bureaux de vote lyonnais

Sections :
  1. Chargement des données (mart.ml_features_bureau_final)
  2. Analyse de corrélation (Pearson) socio-éco vs vote
  3. Classification supervisée multi-modèles (winner_nuance)
  4. Clustering non supervisé des bureaux (K-Means + PCA)

Sorties : src/ml/outputs/*.png
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from dotenv import load_dotenv
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sqlalchemy import create_engine

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

PG_URL = (
    f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}"
    f":{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST', 'localhost')}"
    f":{os.getenv('POSTGRES_PORT', '5432')}"
    f"/{os.getenv('POSTGRES_DB')}"
)

OUTPUTS = Path(__file__).parent / "outputs"
OUTPUTS.mkdir(exist_ok=True)

# Colonnes socio-économiques (année N-1)
SOCIO_ECO_COLS = [
    "delinq_cambriolages_taux",
    "delinq_vols_vehicule_taux",
    "delinq_stupefiants_taux",
    "delinq_violences_sexuelles_taux",
    "delinq_cambriolages_nombre",
    "delinq_vols_vehicule_nombre",
    "delinq_stupefiants_nombre",
    "delinq_violences_sexuelles_nombre",
    "chomage_abc_total",
    "chomage_abc_moins25",
    "chomage_abc_50plus",
]

# Comportements de vote (variables cibles pour la corrélation)
VOTE_BEHAVIOR_COLS = [
    "taux_participation",
    "taux_abstention",
    "taux_exprimes_sur_votants",
    "winner_ratio_exprimes",
    "margin_ratio_exprimes",
]

# Features pour la classification
FEATURE_COLS = [
    "inscrits",
    "taux_participation",
    "taux_abstention",
    "taux_exprimes_sur_votants",
    "nb_candidates",
    "winner_ratio_exprimes",
    "margin_ratio_exprimes",
    # délinquance N-1
    "delinq_cambriolages_taux",
    "delinq_vols_vehicule_taux",
    "delinq_stupefiants_taux",
    "delinq_violences_sexuelles_taux",
    # chômage N-1
    "chomage_abc_total",
    "chomage_abc_moins25",
    "chomage_abc_50plus",
]

TARGET_COL = "winner_nuance"

# Labels lisibles pour les graphiques
SOCIO_LABELS = {
    "delinq_cambriolages_taux": "Cambriolages (taux ‰)",
    "delinq_vols_vehicule_taux": "Vols véhicule (taux ‰)",
    "delinq_stupefiants_taux": "Stupéfiants (taux ‰)",
    "delinq_violences_sexuelles_taux": "Violences sexuelles (taux ‰)",
    "delinq_cambriolages_nombre": "Cambriolages (nb)",
    "delinq_vols_vehicule_nombre": "Vols véhicule (nb)",
    "delinq_stupefiants_nombre": "Stupéfiants (nb)",
    "delinq_violences_sexuelles_nombre": "Violences sexuelles (nb)",
    "chomage_abc_total": "Chômage total (cat. ABC)",
    "chomage_abc_moins25": "Chômage < 25 ans",
    "chomage_abc_50plus": "Chômage 50 ans+",
}

VOTE_LABELS = {
    "taux_participation": "Taux participation",
    "taux_abstention": "Taux abstention",
    "taux_exprimes_sur_votants": "Taux exprimés/votants",
    "winner_ratio_exprimes": "Score du gagnant (%)",
    "margin_ratio_exprimes": "Marge victoire (%)",
}

plt.rcParams.update({"figure.dpi": 140, "font.size": 10})


# ---------------------------------------------------------------------------
# 1. Chargement des données
# ---------------------------------------------------------------------------

def load_data(engine) -> pd.DataFrame:
    query = """
        SELECT * FROM mart.ml_features_bureau_final
        WHERE annee IN (
            SELECT DISTINCT annee
            FROM mart.ml_features_bureau_final
            ORDER BY annee DESC
            LIMIT 3
        )
    """
    df = pd.read_sql(query, engine)
    annees = sorted(df["annee"].dropna().unique().astype(int))
    print(f"[DATA] {len(df):,} lignes | 3 dernières années : {annees}")
    print(f"       Colonnes disponibles : {list(df.columns)}")
    return df


# ---------------------------------------------------------------------------
# 2. Analyse de corrélation
# ---------------------------------------------------------------------------

def analyze_correlations(df: pd.DataFrame) -> None:
    print("\n" + "=" * 60)
    print("2. ANALYSE DE CORRÉLATION SOCIO-ÉCO / COMPORTEMENTS DE VOTE")
    print("=" * 60)

    socio_avail = [c for c in SOCIO_ECO_COLS if c in df.columns]
    vote_avail = [c for c in VOTE_BEHAVIOR_COLS if c in df.columns]

    if not socio_avail or not vote_avail:
        print("[WARN] Colonnes manquantes pour la corrélation.")
        return

    data = df[socio_avail + vote_avail].dropna()
    print(f"  {len(data):,} lignes complètes pour l'analyse")

    # --- Matrice de corrélation Pearson (vote × socio-éco) ---
    corr_matrix = data.corr(method="pearson").loc[vote_avail, socio_avail]

    ax = plt.subplots(figsize=(14, 5))[1]
    sns.heatmap(
        corr_matrix.rename(index=VOTE_LABELS, columns=SOCIO_LABELS),
        annot=True,
        fmt=".2f",
        cmap="RdBu_r",
        center=0,
        vmin=-1,
        vmax=1,
        linewidths=0.4,
        ax=ax,
        cbar_kws={"label": "r de Pearson"},
    )
    ax.set_title(
        "Corrélations de Pearson : facteurs socio-économiques (N-1) vs comportements de vote\n"
        "Bureaux de vote lyonnais",
        fontsize=12,
        pad=12,
    )
    ax.set_xlabel("Facteurs socio-économiques (année N-1)", labelpad=8)
    ax.set_ylabel("Comportements de vote", labelpad=8)
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    path = OUTPUTS / "01_correlation_heatmap.png"
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  [OK] Heatmap → {path}")

    # Top corrélations (valeur absolue)
    flat = corr_matrix.stack().sort_values(key=abs, ascending=False)
    print("\n  Top 10 corrélations (|r| décroissant) :")
    for (vote, socio), val in flat.head(10).items():
        v_lbl = VOTE_LABELS.get(vote, vote)
        s_lbl = SOCIO_LABELS.get(socio, socio)
        print(f"    {v_lbl:35s} ↔ {s_lbl:30s} : r = {val:+.3f}")

    # --- Corrélation Spearman (robustesse) ---
    corr_spearman = data.corr(method="spearman").loc[vote_avail, socio_avail]

    ax = plt.subplots(figsize=(14, 5))[1]
    sns.heatmap(
        corr_spearman.rename(index=VOTE_LABELS, columns=SOCIO_LABELS),
        annot=True,
        fmt=".2f",
        cmap="RdBu_r",
        center=0,
        vmin=-1,
        vmax=1,
        linewidths=0.4,
        ax=ax,
        cbar_kws={"label": "ρ de Spearman"},
    )
    ax.set_title(
        "Corrélations de Spearman : facteurs socio-économiques (N-1) vs comportements de vote\n"
        "Bureaux de vote lyonnais",
        fontsize=12,
        pad=12,
    )
    ax.set_xlabel("Facteurs socio-économiques (année N-1)", labelpad=8)
    ax.set_ylabel("Comportements de vote", labelpad=8)
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    path = OUTPUTS / "02_correlation_spearman.png"
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  [OK] Spearman  → {path}")

    # --- Scatter plots : chômage total vs participation/abstention ---
    if "chomage_abc_total" in df.columns and "taux_participation" in df.columns:
        _scatter_socio_vs_vote(
            df,
            x_col="chomage_abc_total",
            y_col="taux_participation",
            x_label=SOCIO_LABELS["chomage_abc_total"],
            y_label=VOTE_LABELS["taux_participation"],
            out_path=OUTPUTS / "03_scatter_chomage_participation.png",
            color="taux_abstention",
        )
    if "delinq_cambriolages_taux" in df.columns and "taux_participation" in df.columns:
        _scatter_socio_vs_vote(
            df,
            x_col="delinq_cambriolages_taux",
            y_col="taux_participation",
            x_label=SOCIO_LABELS["delinq_cambriolages_taux"],
            y_label=VOTE_LABELS["taux_participation"],
            out_path=OUTPUTS / "04_scatter_cambriolages_participation.png",
            color="chomage_abc_total",
        )


def _scatter_socio_vs_vote(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    x_label: str,
    y_label: str,
    out_path: Path,
    color: str | None = None,
) -> None:
    sub = df[[x_col, y_col] + ([color] if color else [])].dropna()
    ax = plt.subplots(figsize=(8, 6))[1]

    sc_kwargs = dict(alpha=0.4, s=15, edgecolors="none")
    if color and color in sub.columns:
        sc = ax.scatter(sub[x_col], sub[y_col], c=sub[color], cmap="plasma", **sc_kwargs)
        cbar = plt.colorbar(sc, ax=ax)
        cbar.set_label(SOCIO_LABELS.get(color, VOTE_LABELS.get(color, color)))
    else:
        ax.scatter(sub[x_col], sub[y_col], color="steelblue", **sc_kwargs)

    # Droite de régression
    m, b = np.polyfit(sub[x_col], sub[y_col], 1)
    x_range = np.linspace(sub[x_col].min(), sub[x_col].max(), 100)
    ax.plot(x_range, m * x_range + b, color="crimson", linewidth=1.5, label=f"Régression (pente={m:.4f})")

    r = sub[[x_col, y_col]].corr().iloc[0, 1]
    ax.set_title(f"{x_label} vs {y_label}\nr = {r:.3f}", fontsize=11)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.legend(fontsize=9)
    plt.tight_layout()
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()
    print(f"  [OK] Scatter   → {out_path}")


# ---------------------------------------------------------------------------
# 3. Classification supervisée
# ---------------------------------------------------------------------------

def prepare_features(df: pd.DataFrame, min_class_size: int = 5) -> tuple[pd.DataFrame, pd.Series, LabelEncoder]:
    df = df.dropna(subset=[TARGET_COL]).copy()

    # Supprimer les nuances trop rares pour la cross-validation stratifiée
    counts = df[TARGET_COL].value_counts()
    valid_classes = counts[counts >= min_class_size].index
    dropped = counts[counts < min_class_size]
    if not dropped.empty:
        print(f"\n  [INFO] Nuances ignorées (< {min_class_size} bureaux) : {dropped.to_dict()}")
    df = df[df[TARGET_COL].isin(valid_classes)]

    available = [c for c in FEATURE_COLS if c in df.columns]
    X = df[available].fillna(0)
    le = LabelEncoder()
    y = le.fit_transform(df[TARGET_COL])
    print(f"\n  Features utilisées ({len(available)}) : {available}")
    print(f"  {len(le.classes_)} nuances retenues | {len(X):,} bureaux")
    print(f"  Distribution des nuances :\n{df[TARGET_COL].value_counts().to_string()}")
    return X, pd.Series(y, index=X.index), le


def train_models(X: pd.DataFrame, y: pd.Series, le: LabelEncoder) -> RandomForestClassifier:
    print("\n" + "=" * 60)
    print("3. CLASSIFICATION SUPERVISÉE — PRÉDICTION DE LA NUANCE GAGNANTE")
    print("=" * 60)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    models: dict = {
        "Random Forest": RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1),
        "Gradient Boosting": GradientBoostingClassifier(n_estimators=100, random_state=42),
        "Régression Logistique": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=2000, random_state=42)),
        ]),
    }

    print("\n  Cross-validation 5-folds (accuracy) :")
    cv_results: dict[str, np.ndarray] = {}
    for name, model in models.items():
        scores = cross_val_score(model, X, y, cv=cv, scoring="accuracy", n_jobs=-1)
        cv_results[name] = scores
        print(f"    {name:25s} : {scores.mean():.4f} ± {scores.std():.4f}")

    # Boxplot comparaison modèles
    ax = plt.subplots(figsize=(9, 5))[1]
    ax.boxplot(
        list(cv_results.values()),
        tick_labels=list(cv_results.keys()),
        patch_artist=True,
        boxprops=dict(facecolor="#4C72B0", alpha=0.6),
        medianprops=dict(color="crimson", linewidth=2),
    )
    ax.set_title(
        "Comparaison des modèles – Accuracy (5-fold CV)\n"
        "Prédiction de la nuance politique gagnante par bureau de vote",
        fontsize=11,
    )
    ax.set_ylabel("Accuracy")
    ax.set_ylim(0, 1.05)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
    ax.axhline(1 / len(le.classes_), linestyle="--", color="grey", linewidth=1, label="Baseline (aléatoire)")
    ax.legend(fontsize=9)
    plt.tight_layout()
    path = OUTPUTS / "05_model_comparison.png"
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  [OK] Comparaison modèles → {path}")

    # Évaluation finale du Random Forest sur un hold-out 20%
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    rf = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    y_pred = rf.predict(X_test)

    print(f"\n  Random Forest — hold-out 20% ({len(X_test)} bureaux) :")
    print(classification_report(y_test, y_pred, target_names=le.classes_, zero_division=0))

    # Feature importances
    importances = pd.Series(rf.feature_importances_, index=X.columns).sort_values(ascending=False)
    labels = [SOCIO_LABELS.get(c, VOTE_LABELS.get(c, c)) for c in importances.head(15).index]

    ax = plt.subplots(figsize=(10, 6))[1]
    ax.barh(labels, importances.head(15).values, color="steelblue", edgecolor="white")
    ax.invert_yaxis()
    ax.set_title(
        "Importance des features — Random Forest\n(prédiction nuance gagnante par bureau de vote)",
        fontsize=11,
    )
    ax.set_xlabel("Importance (MDI)")
    plt.tight_layout()
    path = OUTPUTS / "06_feature_importances.png"
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  [OK] Feature importances → {path}")

    return rf


# ---------------------------------------------------------------------------
# 4. Clustering K-Means
# ---------------------------------------------------------------------------

def cluster_bureaux(df: pd.DataFrame) -> None:
    print("\n" + "=" * 60)
    print("4. CLUSTERING DES BUREAUX DE VOTE (K-MEANS)")
    print("=" * 60)

    cluster_cols = [c for c in SOCIO_ECO_COLS + ["taux_participation", "taux_abstention"] if c in df.columns]
    data = df[cluster_cols + ([TARGET_COL] if TARGET_COL in df.columns else [])].dropna(subset=cluster_cols)
    print(f"  {len(data):,} bureaux pour le clustering ({len(cluster_cols)} features)")

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(data[cluster_cols])

    # Méthode du coude
    k_range = range(2, 10)
    inertias = []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X_scaled)
        inertias.append(km.inertia_)

    ax = plt.subplots(figsize=(8, 4))[1]
    ax.plot(list(k_range), inertias, marker="o", color="steelblue")
    ax.set_title("Méthode du coude — Clustering des bureaux de vote lyonnais", fontsize=11)
    ax.set_xlabel("Nombre de clusters k")
    ax.set_ylabel("Inertie (SSW)")
    plt.tight_layout()
    path = OUTPUTS / "07_kmeans_elbow.png"
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  [OK] Coude K-Means → {path}")

    # K optimal = 4 (à ajuster selon le coude observé)
    k_opt = 4
    km = KMeans(n_clusters=k_opt, random_state=42, n_init=10)
    clusters = km.fit_predict(X_scaled)

    # Visualisation PCA 2D
    pca = PCA(n_components=2, random_state=42)
    X_pca = pca.fit_transform(X_scaled)
    var_exp = pca.explained_variance_ratio_

    ax = plt.subplots(figsize=(10, 7))[1]
    palette = plt.cm.tab10.colors
    for c in range(k_opt):
        mask = clusters == c
        ax.scatter(
            X_pca[mask, 0],
            X_pca[mask, 1],
            label=f"Cluster {c} ({mask.sum()} bureaux)",
            alpha=0.65,
            s=25,
            color=palette[c],
            edgecolors="none",
        )
    ax.set_title(
        f"Clustering K-Means (k={k_opt}) — Bureaux de vote lyonnais\n"
        f"PCA 2D (variance expliquée : {var_exp.sum():.1%})",
        fontsize=11,
    )
    ax.set_xlabel(f"PC1 ({var_exp[0]:.1%} variance)")
    ax.set_ylabel(f"PC2 ({var_exp[1]:.1%} variance)")
    ax.legend(loc="best", fontsize=9)
    plt.tight_layout()
    path = OUTPUTS / "08_kmeans_pca.png"
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  [OK] PCA K-Means → {path}")

    # Profil des clusters
    data_copy = data.copy()
    data_copy["cluster"] = clusters
    readable_cols = {c: SOCIO_LABELS.get(c, VOTE_LABELS.get(c, c)) for c in cluster_cols}
    profile = (
        data_copy.groupby("cluster")[cluster_cols]
        .mean()
        .rename(columns=readable_cols)
        .round(3)
    )
    print(f"\n  Profil des {k_opt} clusters (moyennes) :")
    print(profile.T.to_string())

    # Heatmap des profils de clusters
    ax = plt.subplots(figsize=(10, 6))[1]
    profile_norm = (profile - profile.min()) / (profile.max() - profile.min() + 1e-9)
    sns.heatmap(
        profile_norm.T,
        annot=profile.T.round(1),
        fmt="g",
        cmap="YlOrRd",
        ax=ax,
        linewidths=0.4,
        cbar_kws={"label": "Valeur normalisée"},
    )
    ax.set_title(
        f"Profil socio-économique des {k_opt} clusters\n(K-Means, bureaux de vote lyonnais)",
        fontsize=11,
    )
    ax.set_xlabel("Cluster")
    ax.set_ylabel("Feature")
    plt.tight_layout()
    path = OUTPUTS / "09_cluster_profiles.png"
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  [OK] Profils clusters → {path}")

    # Croisement cluster × nuance gagnante
    if TARGET_COL in data_copy.columns:
        cross = pd.crosstab(data_copy["cluster"], data_copy[TARGET_COL], normalize="index") * 100
        print(f"\n  Répartition des nuances gagnantes par cluster (%) :")
        print(cross.round(1).to_string())

        ax = plt.subplots(figsize=(10, 5))[1]
        cross.plot.bar(ax=ax, stacked=True, colormap="tab20", edgecolor="white", linewidth=0.3)
        ax.set_title(
            "Répartition des nuances politiques gagnantes par cluster\n(K-Means, bureaux de vote lyonnais)",
            fontsize=11,
        )
        ax.set_xlabel("Cluster")
        ax.set_ylabel("Part des bureaux (%)")
        ax.yaxis.set_major_formatter(mticker.PercentFormatter())
        ax.legend(title="Nuance politique", bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
        plt.xticks(rotation=0)
        plt.tight_layout()
        path = OUTPUTS / "10_cluster_nuances.png"
        plt.savefig(path, bbox_inches="tight")
        plt.close()
        print(f"  [OK] Nuances × clusters → {path}")


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("ML Pipeline — Corrélations socio-éco / vote (Lyon)")
    print("=" * 60)

    engine = create_engine(PG_URL, future=True)
    df = load_data(engine)

    print("\n" + "=" * 60)
    print("2. ANALYSE DE CORRÉLATION")
    print("=" * 60)
    analyze_correlations(df)

    print("\n" + "=" * 60)
    print("3. CLASSIFICATION SUPERVISÉE")
    print("=" * 60)
    X, y, le = prepare_features(df)
    train_models(X, y, le)

    cluster_bureaux(df)

    print(f"\n{'=' * 60}")
    print(f"[DONE] Visualisations sauvegardées dans : {OUTPUTS}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
