"""Étape 5 : calculer le score de toxicité de chaque contrat à partir de ses clauses."""
from config import POINTS, SEUIL_ROUGE, SEUIL_VERT

ORDRE = ["aucune", "faible", "moyenne", "forte"]


def calculer_score(gravites: list[str]) -> dict:
    """Score de densité (0-100), gravité maximale et niveau (vert / orange / rouge)."""
    n = len(gravites)
    total = sum(POINTS[g] for g in gravites)
    densite = round(100 * total / (POINTS["forte"] * n), 1) if n else 0.0
    gravite_max = max(gravites, key=ORDRE.index) if gravites else "aucune"
    if gravite_max == "forte" or densite >= SEUIL_ROUGE:
        niveau = "rouge"
    elif densite < SEUIL_VERT:
        niveau = "vert"
    else:
        niveau = "orange"
    return {
        "nb_toxiques": sum(g != "aucune" for g in gravites),
        "score_densite": densite,
        "gravite_max": gravite_max,
        "niveau": niveau,
    }


if __name__ == "__main__":
    # Exemple : 20 clauses dont 1 forte, 2 moyennes, 1 faible -> 12 points -> densité 12 -> rouge
    print(calculer_score(["forte", "moyenne", "moyenne", "faible"] + ["aucune"] * 16))
