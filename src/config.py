"""Réglages du projet ETICS : chemins, modèles, catégories et barème de toxicité."""
from pathlib import Path

# Chemins (calculés depuis l'emplacement de ce fichier : le projet marche quel que soit le dossier courant)
RACINE = Path(__file__).resolve().parent.parent
DOSSIER_CONTRATS = RACINE / "contrats"
DOSSIER_REFERENCES = RACINE / "references"
DOSSIER_ANNOTATIONS = RACINE / "annotations"
FICHIER_SOURCES = DOSSIER_CONTRATS / "sources.csv"
FICHIER_EXEMPLES = DOSSIER_ANNOTATIONS / "exemples.csv"
FICHIER_ANNOTATIONS = DOSSIER_ANNOTATIONS / "annotations.csv"
BASE_SQLITE = RACINE / "etics.db"
BASE_VECTORIELLE = RACINE / "base_vectorielle"

# Modèles (via Ollama)
OLLAMA_URL = "http://localhost:11434"
MODELE_LLM = "qwen2.5:7b"          # sur un PC modeste : "qwen2.5:3b"
MODELE_EMBEDDING = "bge-m3"
OPTIONS_LLM = {"temperature": 0, "num_ctx": 8192}

# RAG juridique : nombre de références de la loi données au LLM pour juger une clause
NB_REFERENCES = 4

# Catégories de toxicité (inspirées des questions éthiques du sujet)
CATEGORIES = {
    "aucune": "Clause équilibrée, informative ou protectrice du client.",
    "abusive_legale": "Clause qui correspond à une clause abusive de la liste noire ou grise du Code de la consommation.",
    "desequilibre": "Droits ou obligations nettement plus favorables au professionnel (résiliation, modification unilatérale, pénalités...).",
    "transparence": "Clause floue, renvois en cascade, conditions importantes cachées ou difficiles à comprendre.",
    "donnees_personnelles": "Utilisation, partage ou conservation excessive des données personnelles du client.",
    "discrimination": "Traitement différent de certaines catégories de personnes sans justification.",
    "vulnerables": "Clause particulièrement défavorable aux personnes vulnérables (âgées, en difficulté financière...).",
}

# Barème : points par niveau de gravité
POINTS = {"aucune": 0, "faible": 1, "moyenne": 3, "forte": 5}

# Niveaux d'un contrat
SEUIL_VERT = 10    # score de densité < 10 et aucune clause forte  -> vert
SEUIL_ROUGE = 30   # score >= 30 ou au moins une clause forte      -> rouge

# Thèmes à risque, utilisés pour choisir les clauses à annoter en priorité
MOTS_CLES_RISQUE = [
    "modifi", "tarif", "frais", "commission", "résili", "clôtur", "responsab",
    "pénalit", "indemnit", "à tout moment", "sans préavis", "données", "personnel",
    "unilatéral", "exclu", "suspend", "prélev", "intérêt",
]
