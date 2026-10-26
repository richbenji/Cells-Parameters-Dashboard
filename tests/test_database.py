"""Tests de la couche base de données (src/database.py).

Chaque test démarre avec une base vide (fixture clean_db) et fabrique ses
données avec make_df, définies dans conftest.py.
"""
import pytest
from sqlalchemy import text

from src import database as db


def test_import_and_list(make_df):
    # Cas nominal : un dataset importé apparaît dans la liste avec le bon
    # nom et le bon nombre de cellules (cell_count est calculé à l'import).
    dataset_id = db.import_dataset("Donor A", make_df(50))

    datasets = db.list_datasets()
    assert len(datasets) == 1
    assert datasets.loc[0, "id"] == dataset_id
    assert datasets.loc[0, "name"] == "Donor A"
    assert datasets.loc[0, "cell_count"] == 50


def test_duplicate_name_rejected(make_df):
    # Le nom est unique. Le second import doit être refusé avec un message clair,
    # et la base ne doit contenir qu'un seul dataset (rien d'ajouté à moitié).
    db.import_dataset("Donor A", make_df())
    with pytest.raises(ValueError, match="existe déjà"):
        db.import_dataset("Donor A", make_df())
    assert len(db.list_datasets()) == 1


def test_get_cells_returns_requested_columns(make_df):
    # Deux datasets (30 + 20 cellules) : get_cells doit tous les retourner,
    # avec le nom du dataset (colonne "dataset") et les colonnes demandées.
    id_a = db.import_dataset("A", make_df(30, seed=1))
    id_b = db.import_dataset("B", make_df(20, seed=2))

    cols = ["EquivalentCellDiameterFeature", "CircularityFeature"]
    df = db.get_cells([id_a, id_b], cols)

    assert len(df) == 50
    assert set(df["dataset"]) == {"A", "B"}
    assert set(cols) <= set(df.columns)  # "<=" : cols est inclus dans les colonnes


def test_get_cells_same_column_twice(make_df):
    """Cas X == Y dans le scatter plot : pas de colonne dupliquée."""
    # Interroger la même colonne deux fois ne doit pas produire de doublon,
    # sinon Plotly Express échoue ensuite.
    ds = db.import_dataset("A", make_df(10))
    df = db.get_cells([ds], ["CircularityFeature"])
    assert list(df.columns).count("CircularityFeature") == 1


def test_get_cells_rejects_unknown_column(make_df):
    # Test de sécurité : un nom de colonne qui ressemble à une injection SQL
    # doit être refusé par la liste blanche, avant d'atteindre la base.
    ds = db.import_dataset("A", make_df())
    with pytest.raises(ValueError, match="Colonnes inconnues"):
        db.get_cells([ds], ["x; DROP TABLE cells"])


def test_get_cells_empty_selection():
    # Aucun dataset demandé : on obtient un DataFrame vide, pas une erreur SQL
    # (un IN () vide est invalide).
    assert db.get_cells([], ["CircularityFeature"]).empty


def test_delete_removes_cells_too(make_df):
    # Vérifie la suppression en cascade : après avoir supprimé A, ses 30 cellules
    # doivent avoir disparu, et celles de B (20) doivent être intactes.
    id_a = db.import_dataset("A", make_df(30))
    id_b = db.import_dataset("B", make_df(20))

    db.delete_datasets([id_a])

    assert db.list_datasets()["name"].tolist() == ["B"]
    # On interroge la table cells directement, en SQL : on ne passe pas par
    # get_cells, pour contrôler ce qui est réellement stocké.
    with db.engine.connect() as conn:
        remaining = conn.execute(text("SELECT COUNT(*) FROM cells")).scalar()
        orphans = conn.execute(
            text("SELECT COUNT(*) FROM cells WHERE dataset_id = :i"), {"i": id_a}
        ).scalar()
    assert remaining == 20   # seules les cellules de B restent
    assert orphans == 0      # aucune cellule orpheline de A
    assert id_b in db.list_datasets()["id"].tolist()


def test_delete_nothing_is_noop(make_df):
    # Supprimer une liste vide ne doit rien casser ni rien effacer.
    db.import_dataset("A", make_df())
    db.delete_datasets([])
    assert len(db.list_datasets()) == 1


def test_check_db():
    # La base de test est joignable, donc le health check doit dire True.
    assert db.check_db() is True
