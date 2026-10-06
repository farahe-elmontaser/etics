"""Chaîne complète ETICS, à lancer depuis la racine du projet.

    python src/pipeline.py references          # indexer la loi et les recommandations
    python src/pipeline.py decouper            # lire les contrats et les découper en clauses
    python src/pipeline.py annoter --n 200     # préparer un fichier de clauses à annoter à la main
    python src/pipeline.py classer --limite 50 # juger les clauses (reprend là où il s'est arrêté)
    python src/pipeline.py scorer              # calculer le score de chaque contrat
    python src/pipeline.py tout                # decouper + classer + scorer
"""
import argparse
import csv
import random
import time

import base
from classification import charger_exemples, classer_clause
from config import (DOSSIER_ANNOTATIONS, FICHIER_SOURCES, MODELE_LLM,
                    MOTS_CLES_RISQUE)
from decoupage import decouper
from extraction import lire_fichier, lister_contrats
from indexation import indexer_references
from score import calculer_score


def lire_sources() -> dict:
    """Informations sur chaque contrat (banque, pays, type), depuis contrats/sources.csv."""
    if not FICHIER_SOURCES.exists():
        return {}
    with open(FICHIER_SOURCES, encoding="utf-8") as f:
        return {l["fichier"]: l for l in csv.DictReader(f, delimiter=";") if l.get("fichier")}


def etape_decouper(refaire=False):
    sources = lire_sources()
    for f in lister_contrats():
        if base.contrat_existe(f.stem) and not refaire:
            print(f"déjà découpé : {f.name}")
            continue
        texte = lire_fichier(f)
        if len(texte) < 200:
            print(f"⚠️  {f.name} : presque aucun texte (PDF scanné ?), ignoré")
            continue
        clauses = decouper(f.stem, texte)
        base.enregistrer_contrat(f.stem, f.name, sources.get(f.name, {}), clauses)
        print(f"{f.name} : {len(clauses)} clauses")


def etape_classer(limite=None, contrat=None, refaire=False):
    clauses = base.clauses_a_classer(contrat, refaire)
    if limite:
        clauses = clauses[:limite]
    if not clauses:
        print("Aucune clause à classer.")
        return
    exemples = charger_exemples()
    debut = time.time()
    for i, c in enumerate(clauses, 1):
        r = classer_clause(c["texte"], exemples)
        base.enregistrer_classification(c["id"], r, MODELE_LLM)
        marque = f"⚠️  {r['gravite']:<7} {r['categorie']}" if r["toxique"] else "ok"
        moyenne = (time.time() - debut) / i
        print(f"[{i}/{len(clauses)}] {c['id']} : {marque}  (~{moyenne * (len(clauses) - i) / 60:.0f} min restantes)",
              flush=True)


def etape_scorer():
    clauses = base.lire_table("clauses")
    for contrat_id, groupe in clauses.groupby("contrat_id"):
        if groupe["toxique"].isna().any():
            print(f"{contrat_id} : {groupe['toxique'].isna().sum()} clauses pas encore classées, score non calculé")
            continue
        s = calculer_score(groupe["gravite"].tolist())
        base.enregistrer_score(contrat_id, s)
        print(f"{contrat_id} : score {s['score_densite']}, gravité max {s['gravite_max']}, niveau {s['niveau']}")


def etape_annoter(n=200, graine=42):
    """Crée annotations/a_annoter.csv : moitié de clauses sur des thèmes à risque, moitié au hasard."""
    clauses = base.lire_table("clauses")
    if clauses.empty:
        print("Lancez d'abord : python src/pipeline.py decouper")
        return
    risque = clauses[clauses["texte"].str.lower().str.contains("|".join(MOTS_CLES_RISQUE), regex=True)]
    n_risque = min(n // 2, len(risque))
    choix_risque = risque.sample(n_risque, random_state=graine)
    reste = clauses.drop(choix_risque.index)
    choix_hasard = reste.sample(min(n - n_risque, len(reste)), random_state=graine)
    echantillon = list(choix_risque.itertuples()) + list(choix_hasard.itertuples())
    random.Random(graine).shuffle(echantillon)

    DOSSIER_ANNOTATIONS.mkdir(exist_ok=True)
    chemin = DOSSIER_ANNOTATIONS / "a_annoter.csv"
    with open(chemin, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["clause_id", "contrat_id", "texte", "annotateur", "toxique", "categorie", "gravite", "commentaire"])
        for c in echantillon:
            w.writerow([c.id, c.contrat_id, c.texte, "", "", "", "", ""])
    print(f"{len(echantillon)} clauses écrites dans {chemin}")
    print("Remplissez les colonnes, puis enregistrez le fichier sous annotations/annotations.csv")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Chaîne ETICS")
    p.add_argument("etape", choices=["references", "decouper", "annoter", "classer", "scorer", "tout"])
    p.add_argument("--limite", type=int, help="nombre maximum de clauses à classer")
    p.add_argument("--contrat", help="ne traiter qu'un contrat (nom du fichier sans extension)")
    p.add_argument("--n", type=int, default=200, help="nombre de clauses à annoter")
    p.add_argument("--refaire", action="store_true", help="refaire même ce qui est déjà fait")
    a = p.parse_args()

    if a.etape == "references":
        print(indexer_references(), "références juridiques indexées")
    elif a.etape == "decouper":
        etape_decouper(a.refaire)
    elif a.etape == "annoter":
        etape_annoter(a.n)
    elif a.etape == "classer":
        etape_classer(a.limite, a.contrat, a.refaire)
    elif a.etape == "scorer":
        etape_scorer()
    elif a.etape == "tout":
        etape_decouper(a.refaire)
        etape_classer(a.limite, a.contrat, a.refaire)
        etape_scorer()
