"""Base de données structurée (SQLite) : tables contrats et clauses."""
import json
import sqlite3
from datetime import datetime

import pandas as pd

from config import BASE_SQLITE

SCHEMA = """
CREATE TABLE IF NOT EXISTS contrats (
    id TEXT PRIMARY KEY,
    fichier TEXT,
    banque TEXT,
    pays TEXT,
    type_contrat TEXT,
    nb_clauses INTEGER,
    nb_toxiques INTEGER,
    score_densite REAL,
    gravite_max TEXT,
    niveau TEXT,
    date_analyse TEXT
);
CREATE TABLE IF NOT EXISTS clauses (
    id TEXT PRIMARY KEY,
    contrat_id TEXT REFERENCES contrats(id),
    ordre INTEGER,
    numero TEXT,
    texte TEXT,
    toxique INTEGER,           -- NULL tant que la clause n'est pas classée
    categorie TEXT,
    gravite TEXT,
    points INTEGER,
    justification TEXT,
    references_utilisees TEXT, -- liste JSON
    modele TEXT,
    date_classification TEXT
);
"""


def connexion():
    con = sqlite3.connect(BASE_SQLITE)
    con.executescript(SCHEMA)
    return con


def contrat_existe(contrat_id: str) -> bool:
    with connexion() as con:
        return con.execute("SELECT 1 FROM contrats WHERE id = ?", (contrat_id,)).fetchone() is not None


def enregistrer_contrat(contrat_id, fichier, infos: dict, clauses: list[dict]):
    """Enregistre un contrat et ses clauses (remplace une éventuelle version précédente)."""
    with connexion() as con:
        con.execute("DELETE FROM clauses WHERE contrat_id = ?", (contrat_id,))
        con.execute(
            "INSERT OR REPLACE INTO contrats (id, fichier, banque, pays, type_contrat, nb_clauses) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (contrat_id, fichier, infos.get("banque", ""), infos.get("pays", ""),
             infos.get("type_contrat", ""), len(clauses)),
        )
        con.executemany(
            "INSERT INTO clauses (id, contrat_id, ordre, numero, texte) VALUES (?, ?, ?, ?, ?)",
            [(c["id"], c["contrat_id"], c["ordre"], c["numero"], c["texte"]) for c in clauses],
        )


def clauses_a_classer(contrat_id: str | None = None, refaire: bool = False) -> list[dict]:
    requete = "SELECT id, contrat_id, numero, texte FROM clauses WHERE 1=1"
    params = []
    if not refaire:
        requete += " AND toxique IS NULL"
    if contrat_id:
        requete += " AND contrat_id = ?"
        params.append(contrat_id)
    requete += " ORDER BY contrat_id, ordre"
    with connexion() as con:
        lignes = con.execute(requete, params).fetchall()
    return [dict(zip(["id", "contrat_id", "numero", "texte"], l)) for l in lignes]


def enregistrer_classification(clause_id: str, r: dict, modele: str):
    with connexion() as con:
        con.execute(
            "UPDATE clauses SET toxique=?, categorie=?, gravite=?, points=?, justification=?, "
            "references_utilisees=?, modele=?, date_classification=? WHERE id=?",
            (int(r["toxique"]), r["categorie"], r["gravite"], r["points"], r["justification"],
             json.dumps(r["references"], ensure_ascii=False), modele,
             datetime.now().isoformat(timespec="seconds"), clause_id),
        )


def enregistrer_score(contrat_id: str, s: dict):
    with connexion() as con:
        con.execute(
            "UPDATE contrats SET nb_toxiques=?, score_densite=?, gravite_max=?, niveau=?, date_analyse=? "
            "WHERE id=?",
            (s["nb_toxiques"], s["score_densite"], s["gravite_max"], s["niveau"],
             datetime.now().isoformat(timespec="seconds"), contrat_id),
        )


def lire_table(nom: str) -> pd.DataFrame:
    with connexion() as con:
        return pd.read_sql_query(f"SELECT * FROM {nom}", con)
