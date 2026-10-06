"""Tableau de bord ETICS (Streamlit). Lancement : streamlit run dashboard.py"""
import json
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent / "src"))
import base  # noqa: E402

COULEURS = {"vert": "🟢", "orange": "🟠", "rouge": "🔴"}

st.set_page_config(page_title="ETICS – Toxicité des contrats", page_icon="⚖️", layout="wide")
st.title("ETICS – Toxicité des contrats bancaires")

contrats = base.lire_table("contrats")
clauses = base.lire_table("clauses")
if contrats.empty:
    st.info("Aucun contrat analysé. Lancez : python src/pipeline.py tout")
    st.stop()

analyses = contrats.dropna(subset=["niveau"])
c1, c2, c3, c4 = st.columns(4)
c1.metric("Contrats", len(contrats))
c2.metric("Clauses", len(clauses))
c3.metric("Clauses toxiques", int(clauses["toxique"].fillna(0).sum()))
c4.metric("Contrats rouges", int((analyses["niveau"] == "rouge").sum()))

st.subheader("Classement des contrats")
vue = analyses.sort_values("score_densite", ascending=False).copy()
vue["niveau"] = vue["niveau"].map(lambda n: f"{COULEURS.get(n, '')} {n}")
st.dataframe(vue[["id", "banque", "type_contrat", "nb_clauses", "nb_toxiques",
                  "score_densite", "gravite_max", "niveau"]], hide_index=True, use_container_width=True)

if not analyses.empty and analyses["banque"].fillna("").str.len().gt(0).any():
    st.subheader("Score moyen par banque")
    st.bar_chart(analyses.groupby("banque")["score_densite"].mean().sort_values(ascending=False))

toxiques = clauses[clauses["toxique"] == 1]
if not toxiques.empty:
    st.subheader("Clauses toxiques par catégorie")
    st.bar_chart(toxiques["categorie"].value_counts())

st.subheader("Détail d'un contrat")
choix = st.selectbox("Contrat", contrats["id"].tolist())
detail = clauses[(clauses["contrat_id"] == choix) & (clauses["toxique"] == 1)].sort_values("points", ascending=False)
if detail.empty:
    st.success("Aucune clause toxique détectée (ou contrat pas encore classé).")
for _, c in detail.iterrows():
    with st.expander(f"{c['gravite'].upper()} · {c['categorie']} · article {c['numero'] or '-'}"):
        st.write(c["texte"])
        st.markdown(f"**Justification :** {c['justification']}")
        refs = json.loads(c["references_utilisees"] or "[]")
        if refs:
            st.caption("Références : " + ", ".join(refs))
