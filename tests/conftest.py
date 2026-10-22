"""Configuration pytest : base SQLite temporaire, jamais celle de l'application."""
import os
import tempfile

# Doit être défini AVANT tout import de ovizio_app (config lit la variable).
os.environ["OVIZIO_DATA_DIR"] = tempfile.mkdtemp(prefix="ovizio-tests-")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402
from sqlalchemy import text  # noqa: E402

from ovizio_app import database as db  # noqa: E402
from ovizio_app.config import FEATURE_COLUMNS  # noqa: E402


@pytest.fixture(autouse=True)
def clean_db():
    """Base vide avant chaque test."""
    db.init_db()
    with db.engine.begin() as conn:
        conn.execute(text("DELETE FROM datasets"))  # cellules supprimées en cascade
    yield


@pytest.fixture
def make_df():
    """Fabrique un DataFrame synthétique avec les 26 colonnes attendues."""
    def _make(n_rows: int = 50, seed: int = 0) -> pd.DataFrame:
        rng = np.random.default_rng(seed)
        return pd.DataFrame(rng.random((n_rows, len(FEATURE_COLUMNS))),
                            columns=FEATURE_COLUMNS)
    return _make
