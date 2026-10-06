"""Communication avec Ollama : embeddings (bge-m3) et LLM (Qwen) en JSON."""
import json

import requests

from config import MODELE_EMBEDDING, MODELE_LLM, OLLAMA_URL, OPTIONS_LLM


def embed(textes: list[str], lot: int = 16) -> list[list[float]]:
    """Transforme une liste de textes en vecteurs, par lots."""
    vecteurs = []
    for i in range(0, len(textes), lot):
        r = requests.post(f"{OLLAMA_URL}/api/embed",
                          json={"model": MODELE_EMBEDDING, "input": textes[i:i + lot]}, timeout=600)
        r.raise_for_status()
        vecteurs.extend(r.json()["embeddings"])
    return vecteurs


def chat_json(systeme: str, utilisateur: str) -> dict:
    """Envoie un message au LLM et renvoie sa réponse JSON sous forme de dictionnaire."""
    corps = {
        "model": MODELE_LLM,
        "messages": [{"role": "system", "content": systeme},
                     {"role": "user", "content": utilisateur}],
        "stream": False,
        "format": "json",
        "options": OPTIONS_LLM,
    }
    r = requests.post(f"{OLLAMA_URL}/api/chat", json=corps, timeout=900)
    r.raise_for_status()
    contenu = r.json()["message"]["content"]
    try:
        return json.loads(contenu)
    except json.JSONDecodeError:
        return {}
