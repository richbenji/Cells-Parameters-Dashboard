"""Lecture / validation des CSV et utilitaires liés aux features.

Ce module ne connaît ni Dash ni la base de données : il transforme des octets
bruts en DataFrame propre, et fournit des libellés lisibles pour l'interface.
"""
import base64
import io
import re
from pathlib import Path

import pandas as pd

from .config import FEATURE_COLUMNS


def read_csv_bytes(content: bytes) -> pd.DataFrame:
    """Lit un CSV qMod. Le séparateur est détecté automatiquement."""
    # sep=None + engine="python" : pandas devine le séparateur (virgule,
    # point-virgule, tabulation…) avec le module csv.Sniffer de Python.
    # BytesIO fait passer les octets pour un fichier, sans rien écrire sur disque.
    df = pd.read_csv(io.BytesIO(content), sep=None, engine="python")
    # Retire d'éventuels espaces autour des noms de colonnes.
    df.columns = [str(c).strip() for c in df.columns]
    return df


def parse_upload(contents: str) -> bytes:
    """Décode le champ `contents` de dcc.Upload ('data:...;base64,XXXX')."""
    # Dash envoie le fichier sous forme de texte : "data:text/csv;base64,<données>".
    # On coupe à la première virgule pour ne garder que les données encodées,
    # puis on les décode en octets.
    _, b64 = contents.split(",", 1)
    return base64.b64decode(b64)


def validate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Vérifie les colonnes attendues et force le type numérique.

    Retourne le DataFrame réduit aux colonnes de features.
    Lève ValueError avec un message lisible par l'utilisateur.
    """
    # 1. Toutes les colonnes attendues doivent être là (on liste celles qui manquent).
    missing = [c for c in FEATURE_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            "Colonnes manquantes dans le CSV : " + ", ".join(missing)
        )
    # 2. On ne garde que ces colonnes (les éventuelles colonnes en plus sont
    #    ignorées) et on convertit en nombres. errors="coerce" transforme une
    #    valeur illisible en NaN au lieu de faire planter l'import.
    out = df[FEATURE_COLUMNS].apply(pd.to_numeric, errors="coerce")
    # 3. Un fichier avec l'en-tête mais sans ligne n'est pas un dataset.
    if out.empty:
        raise ValueError("Le fichier ne contient aucune cellule.")
    return out


def load_csv(filename: str, content: bytes) -> tuple[str, pd.DataFrame]:
    """Pipeline complet : bytes -> (nom du dataset, DataFrame validé)."""
    df = validate_dataframe(read_csv_bytes(content))
    # Le nom du dataset est le nom du fichier sans extension.
    return Path(filename).stem, df


def feature_label(column: str) -> str:
    """'EquivalentCellDiameterFeature' -> 'Equivalent Cell Diameter'."""
    name = column.removesuffix("Feature")
    # Insère un espace entre une minuscule/un chiffre et une majuscule
    # (frontière de mot dans une écriture CamelCase). "Time [h]" reste inchangé.
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", name)


def feature_options() -> list[dict]:
    """Options pour les dcc.Dropdown."""
    # "label" = texte affiché ; "value" = nom réel de la colonne, qui sera
    # transmis aux callbacks puis à la base.
    return [{"label": feature_label(c), "value": c} for c in FEATURE_COLUMNS]
