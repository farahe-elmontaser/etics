"""Étape 6 : comparer les jugements du LLM aux annotations humaines.

Fichier attendu : annotations/annotations.csv (séparateur ;), avec les colonnes
clause_id ; annotateur ; toxique (oui/non) ; categorie ; gravite
Une même clause peut être annotée par deux personnes (A et B) : on mesure alors leur accord (kappa).
"""
import pandas as pd
from sklearn.metrics import (accuracy_score, cohen_kappa_score, confusion_matrix,
                             f1_score, precision_score, recall_score)

import base
from config import DOSSIER_ANNOTATIONS, FICHIER_ANNOTATIONS


def lire_annotations() -> pd.DataFrame:
    df = pd.read_csv(FICHIER_ANNOTATIONS, sep=";", encoding="utf-8-sig", dtype=str).fillna("")
    df = df[df["toxique"].str.strip() != ""].copy()
    df["toxique"] = df["toxique"].str.strip().str.lower().isin(["oui", "1", "true", "vrai"]).astype(int)
    df["annotateur"] = df["annotateur"].replace("", "A")
    for col in ("categorie", "gravite"):
        df[col] = df[col].str.strip().str.lower()
    return df


def accord_humains(df: pd.DataFrame):
    annotateurs = sorted(df["annotateur"].unique())
    if len(annotateurs) < 2:
        print("Un seul annotateur : pas de kappa entre humains (ajoutez un deuxième annotateur).")
        return
    a, b = annotateurs[:2]
    paire = df[df["annotateur"] == a].merge(df[df["annotateur"] == b], on="clause_id", suffixes=("_a", "_b"))
    if paire.empty:
        print("Aucune clause annotée par les deux annotateurs.")
        return
    k = cohen_kappa_score(paire["toxique_a"], paire["toxique_b"])
    print(f"Accord entre {a} et {b} sur {len(paire)} clauses : kappa = {k:.2f} ({interpreter_kappa(k)})")


def interpreter_kappa(k: float) -> str:
    for seuil, texte in [(0.8, "excellent"), (0.6, "bon"), (0.4, "modéré"), (0.2, "faible")]:
        if k >= seuil:
            return texte
    return "très faible"


def evaluer():
    annotations = lire_annotations()
    print(f"{len(annotations)} annotations lues, {annotations['clause_id'].nunique()} clauses distinctes\n")
    accord_humains(annotations)

    # Référence humaine : le premier annotateur pour chaque clause
    reference = annotations.sort_values("annotateur").drop_duplicates("clause_id")
    predictions = base.lire_table("clauses").dropna(subset=["toxique"])
    df = reference.merge(predictions[["id", "toxique", "categorie", "gravite", "justification"]],
                         left_on="clause_id", right_on="id", suffixes=("_humain", "_llm"))
    if df.empty:
        print("Aucune clause annotée n'a encore été classée par le LLM : lancez l'étape 'classer'.")
        return
    y_h, y_l = df["toxique_humain"], df["toxique_llm"].astype(int)

    print(f"\n=== Toxique ou non : {len(df)} clauses comparées ===")
    print(f"Accuracy  : {accuracy_score(y_h, y_l):.1%}")
    print(f"Précision : {precision_score(y_h, y_l, zero_division=0):.1%}  (parmi les clauses jugées toxiques par le LLM)")
    print(f"Rappel    : {recall_score(y_h, y_l, zero_division=0):.1%}  (parmi les vraies clauses toxiques)")
    print(f"F1-score  : {f1_score(y_h, y_l, zero_division=0):.1%}")
    print(f"Kappa humain / LLM : {cohen_kappa_score(y_h, y_l):.2f} ({interpreter_kappa(cohen_kappa_score(y_h, y_l))})")
    print("\nMatrice de confusion (lignes = humain, colonnes = LLM) :")
    print(pd.DataFrame(confusion_matrix(y_h, y_l, labels=[0, 1]),
                       index=["humain: non toxique", "humain: toxique"],
                       columns=["LLM: non", "LLM: toxique"]))

    toxiques = df[(y_h == 1) & (y_l == 1)]
    if len(toxiques):
        print(f"\nSur les {len(toxiques)} clauses toxiques pour les deux :")
        print(f"  même catégorie : {(toxiques['categorie_humain'] == toxiques['categorie_llm']).mean():.1%}")
        print(f"  même gravité   : {(toxiques['gravite_humain'] == toxiques['gravite_llm']).mean():.1%}")

    desaccords = df[y_h != y_l][["clause_id", "texte", "toxique_humain", "toxique_llm", "justification"]]
    chemin = DOSSIER_ANNOTATIONS / "desaccords.csv"
    desaccords.to_csv(chemin, sep=";", index=False, encoding="utf-8-sig")
    print(f"\n{len(desaccords)} désaccords enregistrés dans {chemin} : lisez-les pour améliorer le prompt.")


if __name__ == "__main__":
    evaluer()
