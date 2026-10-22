"""Configuration centrale de l'application."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("OVIZIO_DATA_DIR", BASE_DIR / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "ovizio.db"
DB_URL = f"sqlite:///{DB_PATH}"

# Colonnes attendues dans les CSV générés par qMod.
# Toutes sont numériques (float).
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
