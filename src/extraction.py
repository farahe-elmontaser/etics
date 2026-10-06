"""Étape 1 : lire les contrats (PDF ou TXT) et en extraire le texte."""
import re
import unicodedata
from pathlib import Path

import pymupdf

from config import DOSSIER_CONTRATS

FORMATS = (".pdf", ".txt")


def nettoyer(texte: str) -> str:
    """Normalise le texte : ligatures (ﬁ -> fi), espaces spéciaux, mots coupés en fin de ligne."""
    texte = unicodedata.normalize("NFKC", texte)
    texte = re.sub(r"(\w)-\n(\w)", r"\1\2", texte)      # mot coupé par un tiret en fin de ligne
    texte = re.sub(r"[ \t]+", " ", texte)
    return texte.strip()


def lire_fichier(chemin) -> str:
    chemin = Path(chemin)
    if chemin.suffix.lower() == ".pdf":
        with pymupdf.open(chemin) as doc:
            texte = "\n".join(page.get_text() for page in doc)
    else:
        texte = chemin.read_text(encoding="utf-8")
    return nettoyer(texte)


def lister_contrats(dossier=DOSSIER_CONTRATS) -> list[Path]:
    return sorted(f for f in Path(dossier).iterdir() if f.suffix.lower() in FORMATS)


if __name__ == "__main__":
    for f in lister_contrats():
        texte = lire_fichier(f)
        alerte = "   ⚠️ texte vide : PDF scanné ?" if len(texte) < 200 else ""
        print(f"{len(texte):>8} caractères | {f.name}{alerte}")
