"""Étape 4 : juger chaque clause (toxique ? catégorie ? gravité ? pourquoi ?) avec le LLM.

Le LLM reçoit : la grille de toxicité, des exemples annotés (few-shot),
les références juridiques les plus proches (RAG) et la clause à juger.
"""
import csv

from config import CATEGORIES, FICHIER_EXEMPLES, MODELE_LLM, POINTS
from indexation import rechercher_references
from ollama_client import chat_json

SYSTEME = f"""Tu es un expert en droit de la consommation qui analyse des contrats bancaires français.
Ta tâche : dire si une clause est TOXIQUE, c'est-à-dire injuste pour le client
(déséquilibre en faveur de la banque, manque de transparence, clause abusive...).

Catégories possibles :
{chr(10).join(f"- {k} : {v}" for k, v in CATEGORIES.items())}

Gravité :
- forte : la clause correspond à une clause de la LISTE NOIRE (toujours abusive)
- moyenne : la clause correspond à une clause de la LISTE GRISE (présumée abusive), ou déséquilibre important
- faible : problème éthique ou de transparence sans base légale claire
- aucune : clause équilibrée

Règles :
1. Une clause qui informe le client, répète une obligation légale ou protège le client N'EST PAS toxique.
2. Appuie-toi en priorité sur les RÉFÉRENCES JURIDIQUES fournies et cite leurs identifiants.
3. Si la clause n'est pas toxique : "toxique": false, "categorie": "aucune", "gravite": "aucune".
4. La justification tient en une ou deux phrases, en français.

Réponds UNIQUEMENT en JSON :
{{"toxique": true ou false, "categorie": "...", "gravite": "...", "justification": "...", "references": ["id", ...]}}"""


def charger_exemples(chemin=FICHIER_EXEMPLES) -> list[dict]:
    """Exemples annotés à la main, utilisés comme modèles dans le prompt (few-shot)."""
    if not chemin.exists():
        return []
    with open(chemin, encoding="utf-8") as f:
        return [l for l in csv.DictReader(f, delimiter=";") if l.get("texte")]


def construire_message(clause: str, references: list[dict], exemples: list[dict]) -> str:
    parties = []
    if references:
        parties.append("RÉFÉRENCES JURIDIQUES :\n" + "\n".join(
            f"[{r['id']}] ({r['source']}) {r['texte']}" for r in references))
    if exemples:
        parties.append("EXEMPLES DÉJÀ ANNOTÉS :\n" + "\n".join(
            f"- Clause : {e['texte']}\n  Réponse : toxique={e['toxique']}, categorie={e['categorie']}, "
            f"gravite={e['gravite']}, justification={e.get('justification', '')}" for e in exemples))
    parties.append(f"CLAUSE À JUGER :\n{clause}")
    return "\n\n".join(parties)


def valider(brut: dict, ids_references: list[str]) -> dict:
    """Corrige une réponse du LLM incomplète ou hors des valeurs autorisées."""
    toxique = str(brut.get("toxique", "false")).lower() in ("true", "1", "oui", "yes")
    categorie = brut.get("categorie", "aucune")
    gravite = brut.get("gravite", "aucune")
    if categorie not in CATEGORIES:
        categorie = "desequilibre" if toxique else "aucune"
    if gravite not in POINTS:
        gravite = "moyenne" if toxique else "aucune"
    if not toxique:
        categorie, gravite = "aucune", "aucune"
    elif gravite == "aucune":       # toxique mais sans gravité : incohérent, on met le minimum
        gravite = "faible"
    refs = [r for r in brut.get("references", []) if r in ids_references]
    return {
        "toxique": toxique,
        "categorie": categorie,
        "gravite": gravite,
        "points": POINTS[gravite],
        "justification": str(brut.get("justification", "")).strip(),
        "references": refs,
    }


def classer_clause(texte: str, exemples: list[dict] | None = None) -> dict:
    references = rechercher_references(texte)
    exemples = charger_exemples() if exemples is None else exemples
    brut = chat_json(SYSTEME, construire_message(texte, references, exemples))
    return valider(brut, [r["id"] for r in references])


if __name__ == "__main__":
    test = "La Banque peut modifier ses tarifs à tout moment, sans en informer le client."
    print(classer_clause(test))
    print("Modèle :", MODELE_LLM)
