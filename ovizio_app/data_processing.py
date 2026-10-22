"""Lecture / validation des CSV et utilitaires liés aux features."""
import base64
import io
import re
from pathlib import Path

import pandas as pd

from .config import FEATURE_COLUMNS


def read_csv_bytes(content: bytes) -> pd.DataFrame:
    """Lit un CSV qMod. Le séparateur est détecté automatiquement."""
    df = pd.read_csv(io.BytesIO(content), sep=None, engine="python")
    df.columns = [str(c).strip() for c in df.columns]
    return df


def parse_upload(contents: str) -> bytes:
    """Décode le champ `contents` de dcc.Upload ('data:...;base64,XXXX')."""
    _, b64 = contents.split(",", 1)
    return base64.b64decode(b64)


def validate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Vérifie les colonnes attendues et force le type numérique.

    Retourne le DataFrame réduit aux colonnes de features.
    Lève ValueError avec un message lisible par l'utilisateur.
    """
    missing = [c for c in FEATURE_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            "Colonnes manquantes dans le CSV : " + ", ".join(missing)
        )
    out = df[FEATURE_COLUMNS].apply(pd.to_numeric, errors="coerce")
    if out.empty:
        raise ValueError("Le fichier ne contient aucune cellule.")
    return out


def load_csv(filename: str, content: bytes) -> tuple[str, pd.DataFrame]:
    """Pipeline complet : bytes -> (nom du dataset, DataFrame validé)."""
    df = validate_dataframe(read_csv_bytes(content))
    return Path(filename).stem, df


def feature_label(column: str) -> str:
    """'EquivalentCellDiameterFeature' -> 'Equivalent Cell Diameter'."""
    name = column.removesuffix("Feature")
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", name)


def feature_options() -> list[dict]:
    """Options pour les dcc.Dropdown."""
    return [{"label": feature_label(c), "value": c} for c in FEATURE_COLUMNS]
