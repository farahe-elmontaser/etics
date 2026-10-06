"""Étape 2 : découper un contrat en clauses.

Les conditions générales numérotent leurs parties de façons très variées :
"Article 3", "ART. 3 -", "3.", "3.2 Frais", "III - Clôture"...
On coupe à chaque titre reconnu ; s'il n'y en a aucun, on coupe par blocs de taille raisonnable.
"""
import re

from langchain_text_splitters import RecursiveCharacterTextSplitter

# Un titre de section, en début de ligne
MOTIF_TITRE = re.compile(
    r"^\s*(?:"
    r"(?:article|art\.)\s*(?P<art>\d+(?:\.\d+)*)"                        # Article 3 / Art. 9.5.6
    r"|(?P<num>\d{1,2}(?:\.\d{1,2}){0,3})\s*[-–.)]?\s+(?=[A-ZÉÈÀÂÎÔÛÇ])"  # 3. Frais / 3.2 Clôture
    r"|(?P<rom>[IVXL]{1,5})\s*[-–.]\s+(?=[A-ZÉÈÀÂÎÔÛÇ])"                 # III - Clôture
    r")",
    re.IGNORECASE | re.MULTILINE,
)

TAILLE_MIN = 120     # en dessous : simple titre, on le fusionne avec la suite
TAILLE_MAX = 1500    # au-dessus : clause trop longue, on la redécoupe

decoupeur = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=150)


def _numero(m: re.Match) -> str:
    return m.group("art") or m.group("num") or m.group("rom") or ""


def decouper(contrat_id: str, texte: str) -> list[dict]:
    """Renvoie la liste des clauses : {id, contrat_id, ordre, numero, texte}."""
    titres = list(MOTIF_TITRE.finditer(texte))
    sections = []
    if titres:
        if titres[0].start() > 0:
            sections.append(("préambule", texte[:titres[0].start()]))
        for i, m in enumerate(titres):
            fin = titres[i + 1].start() if i + 1 < len(titres) else len(texte)
            sections.append((_numero(m), texte[m.start():fin]))
    else:
        sections = [("", texte)]

    # Fusionner les sections trop courtes (souvent un simple titre) avec la suivante
    fusionnees = []
    tampon_num, tampon = "", ""
    for numero, contenu in sections:
        contenu = contenu.strip()
        if not contenu:
            continue
        if tampon:
            contenu = tampon + "\n" + contenu
            numero = tampon_num if tampon_num not in ("", "préambule") else numero
            tampon_num, tampon = "", ""
        if len(contenu) < TAILLE_MIN:
            tampon_num, tampon = numero, contenu
            continue
        fusionnees.append((numero, contenu))
    if tampon:
        if fusionnees:
            n, c = fusionnees[-1]
            fusionnees[-1] = (n, c + "\n" + tampon)
        else:
            fusionnees.append((tampon_num, tampon))

    # Redécouper les clauses trop longues
    clauses = []
    for numero, contenu in fusionnees:
        morceaux = decoupeur.split_text(contenu) if len(contenu) > TAILLE_MAX else [contenu]
        for morceau in morceaux:
            clauses.append({
                "id": f"{contrat_id}_{len(clauses) + 1:04d}",
                "contrat_id": contrat_id,
                "ordre": len(clauses) + 1,
                "numero": numero,
                "texte": " ".join(morceau.split()),   # texte sur une ligne, espaces propres
            })
    return clauses


if __name__ == "__main__":
    from extraction import lire_fichier, lister_contrats
    for f in lister_contrats():
        clauses = decouper(f.stem, lire_fichier(f))
        print(f"{f.name} : {len(clauses)} clauses")
        for c in clauses[:3]:
            print(f"   [{c['numero'] or '-'}] {c['texte'][:100]}…")
