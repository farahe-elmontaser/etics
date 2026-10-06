# ⚖️ ETICS – Détection de la toxicité dans les contrats bancaires

Projet annuel Data – Master 2 EID2, Université Sorbonne Paris Nord.

Système qui transforme des **contrats non structurés** (PDF) en une **base de données structurée**, et qui mesure la **toxicité** de chaque contrat : clauses déséquilibrées, peu transparentes ou abusives. Chaque jugement s'appuie sur des **références juridiques** (Code de la consommation, Commission des clauses abusives) grâce au RAG, et tout fonctionne **en local** avec Ollama.

## Architecture

```
contrats/ (PDF, TXT)          references/ (loi, recommandations CCA)
      │                                 │
      ▼                                 ▼
 1. Extraction (PyMuPDF)          3. Indexation (bge-m3 → ChromaDB)
      │                                 │
      ▼                                 │  4 références les plus proches
 2. Découpage en clauses                │
      │                                 ▼
      └──────────────▶ 4. Classification de chaque clause (Qwen 2.5, JSON)
                              toxique ? catégorie ? gravité ? justification ? références ?
                                        │
                                        ▼
                         5. Score de chaque contrat ──▶ SQLite (tables contrats, clauses)
                                        │
                     6. Évaluation (annotations humaines)  ·  7. Tableau de bord (Streamlit)
```

## Mesure de la toxicité

Chaque clause reçoit des **points** selon sa gravité : aucune = 0, faible = 1, moyenne = 3, forte = 5.

- **forte** : la clause correspond à la liste noire (clauses toujours abusives)
- **moyenne** : liste grise (clauses présumées abusives) ou déséquilibre important
- **faible** : problème éthique ou de transparence sans base légale claire

Pour chaque contrat :

- **Score de densité** (0 à 100) = 100 × somme des points / (5 × nombre de clauses)
- **Gravité maximale** : la clause la plus grave du contrat
- **Niveau** : 🔴 rouge s'il y a une clause forte ou un score ≥ 30 · 🟢 vert si score < 10 · 🟠 orange sinon

Diviser par le nombre de clauses rend comparables des contrats de longueurs différentes ; la gravité maximale garantit qu'une seule clause très abusive suffit à signaler un contrat.

## Installation

```bash
pip install -r requirements.txt
ollama pull qwen2.5:7b
ollama pull bge-m3
```

## Utilisation (depuis la racine du projet)

**1. Préparer les données**

- Mettre les contrats (conditions générales, PDF ou TXT) dans `contrats/` et les décrire dans `contrats/sources.csv`
- Mettre les textes juridiques dans `references/` (voir `references/LISEZ-MOI.md`)
- Compléter les exemples annotés dans `annotations/exemples.csv`

**2. Lancer la chaîne**

```bash
python src/pipeline.py references          # indexer les références juridiques
python src/pipeline.py decouper            # extraire et découper les contrats en clauses
python src/pipeline.py classer --limite 20 # juger 20 clauses (pour tester)
python src/pipeline.py classer             # juger toutes les clauses restantes (reprise automatique)
python src/pipeline.py scorer              # calculer le score de chaque contrat
```

**3. Évaluer**

```bash
python src/pipeline.py annoter --n 200     # crée annotations/a_annoter.csv
# annoter à la main, enregistrer sous annotations/annotations.csv
python src/evaluation.py                   # accuracy, précision, rappel, F1, kappa
```

**4. Visualiser**

```bash
streamlit run dashboard.py
```

## Structure

```
etics/
├── contrats/            # contrats + sources.csv (banque, pays, type, URL, date)
├── references/          # textes juridiques (liste noire, liste grise, recommandations CCA)
├── annotations/         # exemples (few-shot) et annotations humaines
├── src/
│   ├── config.py        # chemins, modèles, catégories, barème
│   ├── ollama_client.py # appels à Ollama (embeddings et LLM)
│   ├── extraction.py    # lecture et nettoyage des PDF / TXT
│   ├── decoupage.py     # découpage en clauses
│   ├── indexation.py    # RAG juridique (ChromaDB)
│   ├── classification.py# jugement de chaque clause par le LLM
│   ├── score.py         # score de chaque contrat
│   ├── base.py          # base SQLite (contrats, clauses)
│   ├── pipeline.py      # chaîne complète
│   └── evaluation.py    # comparaison avec les annotations humaines
└── dashboard.py         # tableau de bord Streamlit
```

## Limites

Le jugement du LLM n'a de valeur qu'après **validation** sur des clauses annotées par des humains. La notion de clause abusive dépend du **droit applicable** : les références doivent correspondre au pays des contrats. Ce système est une **aide à l'analyse** et ne remplace pas l'avis d'un juriste.
