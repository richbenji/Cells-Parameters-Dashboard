"""Accès à la base SQLite (SQL explicite via SQLAlchemy Core).

Schéma :
    datasets(id, name UNIQUE, cell_count, imported_at)
    cells(dataset_id -> datasets.id, <26 colonnes de features>)
"""
import pandas as pd
from sqlalchemy import bindparam, create_engine, event, text

from .config import DB_URL, FEATURE_COLUMNS

engine = create_engine(DB_URL, future=True)


@event.listens_for(engine, "connect")
def _enable_foreign_keys(dbapi_conn, _):
    # SQLite n'active pas les clés étrangères par défaut
    dbapi_conn.execute("PRAGMA foreign_keys = ON")


def _quote(col: str) -> str:
    return '"' + col.replace('"', '""') + '"'


def init_db() -> None:
    """Crée les tables si elles n'existent pas."""
    feature_ddl = ",\n        ".join(f"{_quote(c)} REAL" for c in FEATURE_COLUMNS)
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS datasets (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL UNIQUE,
                cell_count  INTEGER NOT NULL,
                imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS cells (
                dataset_id INTEGER NOT NULL
                    REFERENCES datasets(id) ON DELETE CASCADE,
                {feature_ddl}
            )
        """))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_cells_dataset ON cells(dataset_id)"
        ))


def dataset_exists(name: str) -> bool:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT 1 FROM datasets WHERE name = :n"), {"n": name}
        ).first()
    return row is not None


def import_dataset(name: str, df: pd.DataFrame) -> int:
    """Insère un dataset et ses cellules. Retourne l'id du dataset.

    Lève ValueError si le nom existe déjà.
    """
    if dataset_exists(name):
        raise ValueError(f"Un dataset nommé « {name} » existe déjà.")

    with engine.begin() as conn:  # transaction : tout ou rien
        result = conn.execute(
            text("INSERT INTO datasets (name, cell_count) VALUES (:n, :c)"),
            {"n": name, "c": len(df)},
        )
        dataset_id = result.lastrowid
        to_insert = df[FEATURE_COLUMNS].copy()
        to_insert.insert(0, "dataset_id", dataset_id)
        to_insert.to_sql("cells", conn, if_exists="append", index=False,
                         chunksize=500)
    return dataset_id


def list_datasets() -> pd.DataFrame:
    """Colonnes : id, name, cell_count, imported_at."""
    with engine.connect() as conn:
        return pd.read_sql(
            text("SELECT id, name, cell_count, imported_at "
                 "FROM datasets ORDER BY id"),
            conn,
        )


def delete_datasets(ids: list[int]) -> None:
    """Supprime des datasets (les cellules partent via ON DELETE CASCADE)."""
    if not ids:
        return
    stmt = text("DELETE FROM datasets WHERE id IN :ids").bindparams(
        bindparam("ids", expanding=True)
    )
    with engine.begin() as conn:
        conn.execute(stmt, {"ids": [int(i) for i in ids]})


def get_cells(dataset_ids: list[int], columns: list[str]) -> pd.DataFrame:
    """Retourne les colonnes demandées + dataset_id + dataset (nom).

    Les noms de colonnes sont validés contre une liste blanche,
    ce qui évite toute injection SQL.
    """
    if not dataset_ids:
        return pd.DataFrame(columns=["dataset_id", "dataset", *columns])
    unknown = [c for c in columns if c not in FEATURE_COLUMNS]
    if unknown:
        raise ValueError(f"Colonnes inconnues : {unknown}")

    cols_sql = ", ".join(f"c.{_quote(c)}" for c in columns)
    stmt = text(
        f"SELECT c.dataset_id, d.name AS dataset, {cols_sql} "
        "FROM cells c JOIN datasets d ON d.id = c.dataset_id "
        "WHERE c.dataset_id IN :ids"
    ).bindparams(bindparam("ids", expanding=True))
    with engine.connect() as conn:
        return pd.read_sql(stmt, conn,
                           params={"ids": [int(i) for i in dataset_ids]})


def check_db() -> bool:
    """Utilisé plus tard par le health check."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
