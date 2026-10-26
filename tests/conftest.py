"""Configuration pytest : base SQLite temporaire, jamais celle de l'application.

pytest charge automatiquement ce fichier avant les tests. Les fixtures qu'il
définit (clean_db, make_df) sont utilisables dans tous les fichiers de tests,
sans import.
"""
import os
import tempfile

# Doit être défini AVANT tout import de src (config lit la variable).
# config.py crée le dossier et l'engine SQLAlchemy dès l'import : si on
# importait src d'abord, les tests écriraient dans ta vraie base data/.
# mkdtemp crée un dossier temporaire unique, propre à chaque lancement de pytest.
os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="tests-")

# Ces imports viennent volontairement après la ligne ci-dessus ; "noqa: E402"
# empêche l'éditeur de signaler « import pas en haut du fichier ».
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402
from sqlalchemy import text  # noqa: E402

from src import database as db  # noqa: E402
from src.config import FEATURE_COLUMNS  # noqa: E402


# autouse=True : cette fixture s'applique automatiquement à CHAQUE test,
# sans qu'il ait à la demander dans ses paramètres.
@pytest.fixture(autouse=True)
def clean_db():
    """Base vide avant chaque test."""
    # Les tests sont ainsi indépendants : un test ne peut pas être faussé par
    # les données laissées par un autre, quel que soit l'ordre d'exécution.
    db.init_db()
    with db.engine.begin() as conn:
        conn.execute(text("DELETE FROM datasets"))  # cellules supprimées en cascade
    # "yield" sépare la préparation (avant) du nettoyage (après). Ici il n'y a
    # rien à nettoyer après : le nettoyage se fait avant le test suivant.
    yield


@pytest.fixture
def make_df():
    """Fabrique un DataFrame synthétique avec les 26 colonnes attendues."""
    # La fixture retourne une fonction, pour que chaque test choisisse le
    # nombre de lignes et la graine (seed) : même seed = mêmes valeurs, donc
    # des tests reproductibles ; seeds différentes = datasets différents.
    def _make(n_rows: int = 50, seed: int = 0) -> pd.DataFrame:
        rng = np.random.default_rng(seed)
        return pd.DataFrame(rng.random((n_rows, len(FEATURE_COLUMNS))),
                            columns=FEATURE_COLUMNS)
    return _make
