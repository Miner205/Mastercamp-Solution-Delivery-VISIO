import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

from database import get_db_as_df

DB_NAME = "visio_database.db"
DATA_FOLDER = "Data/web_app"

# Features numériques disponibles dans la base + libellés lisibles
FEATURES = ["file_size", "width", "height", "avg_r", "avg_g", "avg_b", "ai_confidence"]
FEATURE_LABELS = {
    "file_size": "Taille du fichier (octets)",
    "width": "Largeur (px)",
    "height": "Hauteur (px)",
    "avg_r": "Rouge moyen",
    "avg_g": "Vert moyen",
    "avg_b": "Bleu moyen",
    "ai_confidence": "Confiance IA",
}

# Palette cohérente vide / pleine (s'adapte si d'autres libellés)
PALETTE = {"vide": "#2ca02c", "pleine": "#d62728"}


def _prepare(df):
    """Ne garde que les images réellement annotées manuellement et nettoie les features."""
    df = df.copy()
    df = df[df["manual_annotation"].notna() & (df["manual_annotation"].astype(str).str.strip() != "")]
    for col in FEATURES:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _present_features(df):
    return [f for f in FEATURES if f in df.columns and df[f].notna().any()]


def show():
    st.title("Statistiques")

    df_raw = get_db_as_df()
    st.metric("Nombre d'images analysées :", len(df_raw))

    if len(df_raw) == 0:
        st.info("Aucune image en base pour le moment.")
        return

    df = _prepare(df_raw)
    if len(df) == 0:
        st.warning("Aucune image annotée manuellement pour l'instant : impossible de croiser les features avec le statut vide/pleine.")
        return

    classes = sorted(df["manual_annotation"].unique().tolist())
    features = _present_features(df)
    palette = {c: PALETTE.get(str(c).lower(), None) for c in classes}

    tab_rep, tab_dist, tab_rel, tab_corr, tab_couleur, tab_ia = st.tabs(
        ["Répartition", "Distributions par classe", "Relations entre features",
         "Corrélations", "Couleurs moyennes", "IA vs Manuel"]
    )

    # ------------------------------------------------------------------ #
    # 1. Répartition vide / pleine
    # ------------------------------------------------------------------ #
    with tab_rep:
        st.subheader("Répartition des annotations manuelles")
        counts = df["manual_annotation"].value_counts()
        st.bar_chart(counts, x_label="Annotation manuelle", y_label="Nombre d'images")
        cols = st.columns(len(counts))
        for col, (label, n) in zip(cols, counts.items()):
            col.metric(str(label), n, f"{100 * n / counts.sum():.0f} %")

    # ------------------------------------------------------------------ #
    # 2. Distribution de chaque feature selon vide / pleine
    # ------------------------------------------------------------------ #
    with tab_dist:
        st.subheader("Comment chaque feature se répartit selon le statut")
        feat = st.selectbox(
            "Feature à analyser",
            features,
            format_func=lambda x: FEATURE_LABELS.get(x, x),
            key="dist_feat",
        )
        sub = df[["manual_annotation", feat]].dropna()

        c1, c2 = st.columns(2)
        with c1:
            fig, ax = plt.subplots()
            sns.boxplot(data=sub, x="manual_annotation", y=feat, ax=ax, palette=palette)
            ax.set_xlabel("Annotation manuelle")
            ax.set_ylabel(FEATURE_LABELS.get(feat, feat))
            ax.set_title("Box plot")
            st.pyplot(fig)
        with c2:
            fig, ax = plt.subplots()
            sns.histplot(data=sub, x=feat, hue="manual_annotation", kde=True,
                         palette=palette, ax=ax, element="step", common_norm=False)
            ax.set_xlabel(FEATURE_LABELS.get(feat, feat))
            ax.set_title("Distribution")
            st.pyplot(fig)

        # Tableau récap moyenne / médiane par classe
        recap = sub.groupby("manual_annotation")[feat].agg(["mean", "median", "std", "count"])
        recap.columns = ["Moyenne", "Médiane", "Écart-type", "Effectif"]
        st.dataframe(recap.style.format("{:.2f}"))

    # ------------------------------------------------------------------ #
    # 3. Relation entre deux features, colorée par le statut
    # ------------------------------------------------------------------ #
    with tab_rel:
        st.subheader("Nuage de points entre deux features")
        c1, c2 = st.columns(2)
        x_feat = c1.selectbox("Axe X", features,
                              format_func=lambda x: FEATURE_LABELS.get(x, x), key="rel_x")
        y_feat = c2.selectbox("Axe Y", features, index=min(1, len(features) - 1),
                              format_func=lambda x: FEATURE_LABELS.get(x, x), key="rel_y")
        sub = df[["manual_annotation", x_feat, y_feat]].dropna()
        st.scatter_chart(sub, x=x_feat, y=y_feat, color="manual_annotation")
        st.caption("Si les couleurs (vide/pleine) se séparent visuellement, ces deux features "
                   "permettent de distinguer une poubelle vide d'une pleine.")

    # ------------------------------------------------------------------ #
    # 4. Corrélations
    # ------------------------------------------------------------------ #
    with tab_corr:
        st.subheader("Corrélations entre features")
        corr = df[features].corr()
        fig, ax = plt.subplots()
        sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0,
                    vmin=-1, vmax=1, ax=ax,
                    xticklabels=[FEATURE_LABELS.get(f, f) for f in features],
                    yticklabels=[FEATURE_LABELS.get(f, f) for f in features])
        st.pyplot(fig)

        # Corrélation de chaque feature avec le fait d'être "pleine" (si binaire)
        if len(classes) == 2:
            full_label = next((c for c in classes if str(c).lower() == "pleine"), classes[-1])
            target = (df["manual_annotation"] == full_label).astype(int)
            link = df[features].apply(lambda col: col.corr(target)).sort_values()
            st.subheader(f"Lien de chaque feature avec « {full_label} »")
            fig, ax = plt.subplots()
            colors = ["#d62728" if v > 0 else "#1f77b4" for v in link.values]
            ax.barh([FEATURE_LABELS.get(f, f) for f in link.index], link.values, color=colors)
            ax.axvline(0, color="black", linewidth=0.8)
            ax.set_xlabel(f"Corrélation avec « {full_label} »  (−1 → +1)")
            st.pyplot(fig)
            st.caption("Plus la barre est longue, plus la feature est liée au statut. "
                       "Positif = valeur élevée associée à une poubelle pleine ; négatif = associée à vide.")
        else:
            st.info("Le lien feature/cible n'est calculé que pour un cas binaire (vide vs pleine).")

    # ------------------------------------------------------------------ #
    # 5. Couleur moyenne par classe
    # ------------------------------------------------------------------ #
    with tab_couleur:
        st.subheader("Couleur moyenne des images selon le statut")
        if all(c in df.columns for c in ["avg_r", "avg_g", "avg_b"]):
            means = df.groupby("manual_annotation")[["avg_r", "avg_g", "avg_b"]].mean()
            cols = st.columns(len(means))
            for col, (label, row) in zip(cols, means.iterrows()):
                r, g, b = int(row["avg_r"]), int(row["avg_g"]), int(row["avg_b"])
                col.markdown(f"**{label}**")
                col.markdown(
                    f"<div style='background-color: rgb({r},{g},{b}); "
                    f"height:80px; border-radius:8px; border:1px solid #ccc;'></div>",
                    unsafe_allow_html=True,
                )
                col.caption(f"RGB({r}, {g}, {b})")
            st.markdown("<br>", unsafe_allow_html=True)
            st.bar_chart(means)
            st.caption("Une poubelle pleine est souvent plus sombre / plus colorée par les déchets "
                       "qu'une poubelle vide : ces moyennes RGB permettent de le vérifier.")
        else:
            st.info("Colonnes de couleur (avg_r, avg_g, avg_b) absentes.")

    # ------------------------------------------------------------------ #
    # 6. IA vs annotation manuelle
    # ------------------------------------------------------------------ #
    with tab_ia:
        st.subheader("Confiance de l'IA selon le statut réel")
        if "ai_confidence" in df.columns and df["ai_confidence"].notna().any():
            sub = df[["manual_annotation", "ai_confidence"]].dropna()
            fig, ax = plt.subplots()
            sns.boxplot(data=sub, x="manual_annotation", y="ai_confidence", ax=ax, palette=palette)
            ax.set_xlabel("Annotation manuelle")
            ax.set_ylabel("Confiance IA")
            st.pyplot(fig)

        if "ai_annotation" in df.columns and df["ai_annotation"].notna().any():
            st.subheader("Accord IA / Manuel")
            comp = df.dropna(subset=["ai_annotation"])
            comp = comp[comp["ai_annotation"].astype(str).str.strip() != ""]
            if len(comp) > 0:
                matrix = pd.crosstab(comp["manual_annotation"], comp["ai_annotation"])
                fig, ax = plt.subplots()
                sns.heatmap(matrix, annot=True, fmt="d", cmap="Blues", ax=ax)
                ax.set_xlabel("Annotation IA")
                ax.set_ylabel("Annotation manuelle")
                st.pyplot(fig)
                accuracy = (comp["ai_annotation"] == comp["manual_annotation"]).mean()
                st.metric("Taux d'accord IA / Manuel", f"{accuracy * 100:.1f} %")
            else:
                st.info("Pas encore d'annotations IA exploitables.")