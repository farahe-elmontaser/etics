"""Étape 3 : indexer les références juridiques (loi, recommandations) dans ChromaDB.

Format des fichiers de references/ :
- un fichier .txt par source (liste noire, liste grise, recommandation de la CCA...)
- les lignes qui commencent par # sont des commentaires (source, URL, date)
- les références sont séparées par une ligne vide
"""
from pathlib import Path

import chromadb

from config import BASE_VECTORIELLE, DOSSIER_REFERENCES, NB_REFERENCES
from ollama_client import embed

COLLECTION = "references_juridiques"


def _client():
    return chromadb.PersistentClient(path=str(BASE_VECTORIELLE))


def lire_references(dossier=DOSSIER_REFERENCES) -> list[dict]:
    references = []
    for fichier in sorted(Path(dossier).glob("*.txt")):
        lignes = [l for l in fichier.read_text(encoding="utf-8").splitlines() if not l.startswith("#")]
        blocs = [b.strip() for b in "\n".join(lignes).split("\n\n")]
        for i, bloc in enumerate(b for b in blocs if b):
            references.append({"id": f"{fichier.stem}_{i + 1:02d}",
                               "source": fichier.stem,
                               "texte": " ".join(bloc.split())})
    return references


def indexer_references() -> int:
    """Recrée la collection à partir des fichiers de references/. Renvoie le nombre de références."""
    client = _client()
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
    references = lire_references()
    if references:
        collection.add(
            ids=[r["id"] for r in references],
            documents=[r["texte"] for r in references],
            metadatas=[{"source": r["source"]} for r in references],
            embeddings=embed([r["texte"] for r in references]),
        )
    return len(references)


def rechercher_references(texte: str, k: int = NB_REFERENCES) -> list[dict]:
    """Renvoie les k références juridiques les plus proches d'une clause."""
    try:
        collection = _client().get_collection(COLLECTION)
    except Exception:
        return []
    n = collection.count()
    if n == 0:
        return []
    res = collection.query(query_embeddings=embed([texte]), n_results=min(k, n))
    return [{"id": i, "texte": d, "source": m["source"]}
            for i, d, m in zip(res["ids"][0], res["documents"][0], res["metadatas"][0])]


if __name__ == "__main__":
    print(indexer_references(), "références indexées")
