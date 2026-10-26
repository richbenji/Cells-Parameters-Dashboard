"""Configuration centrale de l'application.

Ce module est importé par presque tous les autres et ne dépend d'aucun
d'entre eux : cela évite les imports circulaires.
"""
import os
from pathlib import Path

# Racine du projet. Ce fichier est dans src/, donc on remonte de deux niveaux :
# config.py -> src/ -> racine du projet.
BASE_DIR = Path(__file__).resolve().parent.parent

# Dossier de la base de données. Par défaut ./data, mais la variable
# d'environnement DATA_DIR permet de le changer sans toucher au code :
#   - le conteneur la fixe à /data (monté en volume) ;
#   - les tests la fixent à un dossier temporaire.
DATA_DIR = Path(os.environ.get("DATA_DIR", BASE_DIR / "data"))

# Effet de bord à l'import : le dossier est créé s'il n'existe pas.
# C'est pour ça que les tests doivent définir DATA_DIR AVANT d'importer src.
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "data.db"
# URL SQLAlchemy. Le chemin absolu commence déjà par "/", d'où les 4 "/" au total.
DB_URL = f"sqlite:///{DB_PATH}"

# Colonnes attendues dans les CSV générés par qMod.
# Toutes sont numériques (float). Cette liste sert à trois choses :
#   1. valider les CSV importés (data_processing.validate_dataframe) ;
#   2. créer la table "cells" (database.init_db) ;
#   3. servir de liste blanche des noms de colonnes autorisés dans les
#      requêtes SQL (database.get_cells) et d'options aux menus déroulants.
FEATURE_COLUMNS = [
    "AspectRatioFeature",
    "CellAreaFeature",
    "CenterOfMassHorizontalPositionFeature",
    "CenterOfMassVerticalPositionFeature",
    "CircularityFeature",
    "CompactnessFeature",
    "ElongatednessFeature",
    "ElongationFeature",
    "EquivalentCellDiameterFeature",
    "HuMoment1Feature",
    "OpticalHeightMeanInMicronFeature",
    "OpticalHeightMeanNormalizedFeature",
    "OpticalHeightStandardDeviationInMicronFeature",
    "OpticalVolumeFeature",
    "PerimeterFeature",
    "PhaseContrastFeature",
    "PhaseCorrelationFeature",
    "PhaseEntropyFeature",
    "PhaseHomogeneityFeature",
    "PhaseSkewnessFeature",
    "PhaseSmoothnessFeature",
    "PhaseUniformityFeature",
    "RadiusMeanFeature",
    "RadiusVarianceFeature",
    "RadiusVarianceNormalizedFeature",
    "Time [h]",
]

# Valeurs par défaut des menus déroulants (cf. maquette)
DEFAULT_X = "EquivalentCellDiameterFeature"
DEFAULT_Y = "CircularityFeature"
