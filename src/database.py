"""Accès à la base SQLite (SQL explicite via SQLAlchemy Core).

Schéma :
    datasets(id, name UNIQUE, cell_count, imported_at)
    cells(dataset_id -> datasets.id, <26 colonnes de features>)

Toutes les requêtes SQL de l'application sont ici. Les autres modules
appellent ces fonctions et ne manipulent jamais SQL directement.
"""
import pandas as pd
from sqlalchemy import bindparam, create_engine, event, text

from .config import DB_URL, FEATURE_COLUMNS

# L'engine gère le fichier SQLite et un petit pool de connexions.
# Il est créé une seule fois, à l'import du module.
engine = create_engine(DB_URL, future=True)


@event.listens_for(engine, "connect")
def _enable_foreign_keys(dbapi_conn, _):
    # SQLite n'applique PAS les clés étrangères par défaut, et ce réglage est
    # propre à chaque connexion. Sans cette ligne, ON DELETE CASCADE ne ferait
    # rien et supprimer un dataset laisserait ses cellules orphelines.
    dbapi_conn.execute("PRAGMA foreign_keys = ON")


def _quote(col: str) -> str:
    # Entoure un nom de colonne de guillemets doubles pour SQL ("Time [h]" a un
    # espace et des crochets). Un guillemet interne est doublé, selon la norme SQL.
    return '"' + col.replace('"', '""') + '"'


def init_db() -> None:
    """Crée les tables si elles n'existent pas."""
    # Les 26 colonnes de features sont générées depuis config : on ne les
    # recopie pas à la main, donc la table suit toujours la liste.
    feature_ddl = ",\n        ".join(f"{_quote(c)} REAL" for c in FEATURE_COLUMNS)
    # engine.begin() ouvre une transaction : validée à la sortie du bloc,
    # annulée si une exception survient.
    with engine.begin() as conn:
        # AUTOINCREMENT : un id supprimé n'est jamais réattribué. C'est ce qui
        # garde la couleur d'un dataset stable dans les graphiques.
        # UNIQUE sur name : empêche d'importer deux fois le même fichier.
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS datasets (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL UNIQUE,
                cell_count  INTEGER NOT NULL,
                imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        # Une ligne par cellule. ON DELETE CASCADE : supprimer un dataset
        # supprime automatiquement ses cellules.
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS cells (
                dataset_id INTEGER NOT NULL
                    REFERENCES datasets(id) ON DELETE CASCADE,
                {feature_ddl}
            )
        """))
        # Index : accélère les recherches et les suppressions par dataset_id
        # (sans lui, SQLite parcourt toute la table).
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_cells_dataset ON cells(dataset_id)"
        ))


def dataset_exists(name: str) -> bool:
    # ":n" est un paramètre lié : la valeur est transmise séparément de la
    # requête, jamais collée dans le texte SQL (protection contre l'injection).
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
        # 1. On crée la ligne du dataset et on récupère l'id généré.
        result = conn.execute(
            text("INSERT INTO datasets (name, cell_count) VALUES (:n, :c)"),
            {"n": name, "c": len(df)},
        )
        dataset_id = result.lastrowid
        # 2. On ajoute la colonne dataset_id en première position, puis
        #    pandas insère toutes les cellules. On lui passe la MÊME connexion :
        #    les deux étapes font partie de la même transaction, donc si
        #    l'insertion des cellules échoue, le dataset n'est pas créé non plus.
        #    chunksize=500 : insertion par paquets de 500 lignes.
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
    # "expanding=True" : SQLAlchemy transforme ":ids" en une liste de paramètres
    # (?, ?, ?) de la bonne longueur. C'est la façon sûre d'écrire un IN (...).
    stmt = text("DELETE FROM datasets WHERE id IN :ids").bindparams(
        bindparam("ids", expanding=True)
    )
    with engine.begin() as conn:
        # int(i) : convertit les types numpy éventuels en entiers Python.
        conn.execute(stmt, {"ids": [int(i) for i in ids]})


def get_cells(dataset_ids: list[int], columns: list[str]) -> pd.DataFrame:
    """Retourne les colonnes demandées + dataset_id + dataset (nom).

    Les noms de colonnes sont validés contre une liste blanche,
    ce qui évite toute injection SQL.
    """
    if not dataset_ids:
        return pd.DataFrame(columns=["dataset_id", "dataset", *columns])
    # Une valeur peut être liée par paramètre, mais pas un NOM de colonne.
    # On doit donc l'écrire dans le texte de la requête, ce qui n'est sûr que
    # si le nom est vérifié avant : seules les colonnes connues passent.
    unknown = [c for c in columns if c not in FEATURE_COLUMNS]
    if unknown:
        raise ValueError(f"Colonnes inconnues : {unknown}")

    cols_sql = ", ".join(f"c.{_quote(c)}" for c in columns)
    # JOIN : on rattache à chaque cellule le nom de son dataset ("dataset"),
    # qui servira à colorer les points dans les graphiques.
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
    # Requête la plus simple possible : si elle passe, la base est joignable.
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
