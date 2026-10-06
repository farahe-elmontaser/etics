# Références juridiques

Ce dossier contient les textes qui servent de **base de jugement** au LLM (RAG juridique).

## Quoi mettre

| Fichier | Contenu | Où le trouver |
|---|---|---|
| `liste_noire.txt` | Clauses **toujours** abusives (article R212-1 du Code de la consommation) | legifrance.gouv.fr |
| `liste_grise.txt` | Clauses **présumées** abusives (article R212-2) | legifrance.gouv.fr |
| `cca_*.txt` | Recommandations de la Commission des clauses abusives (une par fichier, ex. `cca_banque.txt`) | clauses-abusives.fr |

## Format

- Les lignes qui commencent par `#` sont des commentaires (source, URL, date) : elles sont ignorées.
- **Une référence par paragraphe**, séparée de la suivante par **une ligne vide**.
- Copiez le texte **officiel**, sans le reformuler.

Exemple :

```
# Source : Code de la consommation, article R212-1 – Légifrance – consulté le 06/10/2026

1° Constater l'adhésion du non-professionnel ou du consommateur à des clauses qui ne figurent pas dans l'écrit qu'il accepte...

2° Restreindre l'obligation pour le professionnel de respecter les engagements pris par ses préposés...
```

Après chaque modification : `python src/pipeline.py references`
