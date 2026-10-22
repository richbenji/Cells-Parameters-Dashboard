import pytest
from sqlalchemy import text

from ovizio_app import database as db


def test_import_and_list(make_df):
    dataset_id = db.import_dataset("Donor A", make_df(50))

    datasets = db.list_datasets()
    assert len(datasets) == 1
    assert datasets.loc[0, "id"] == dataset_id
    assert datasets.loc[0, "name"] == "Donor A"
    assert datasets.loc[0, "cell_count"] == 50


def test_duplicate_name_rejected(make_df):
    db.import_dataset("Donor A", make_df())
    with pytest.raises(ValueError, match="existe déjà"):
        db.import_dataset("Donor A", make_df())
    assert len(db.list_datasets()) == 1


def test_get_cells_returns_requested_columns(make_df):
    id_a = db.import_dataset("A", make_df(30, seed=1))
    id_b = db.import_dataset("B", make_df(20, seed=2))

    cols = ["EquivalentCellDiameterFeature", "CircularityFeature"]
    df = db.get_cells([id_a, id_b], cols)

    assert len(df) == 50
    assert set(df["dataset"]) == {"A", "B"}
    assert set(cols) <= set(df.columns)


def test_get_cells_same_column_twice(make_df):
    """Cas X == Y dans le scatter plot : pas de colonne dupliquée."""
    ds = db.import_dataset("A", make_df(10))
    df = db.get_cells([ds], ["CircularityFeature"])
    assert list(df.columns).count("CircularityFeature") == 1


def test_get_cells_rejects_unknown_column(make_df):
    ds = db.import_dataset("A", make_df())
    with pytest.raises(ValueError, match="Colonnes inconnues"):
        db.get_cells([ds], ["x; DROP TABLE cells"])


def test_get_cells_empty_selection():
    assert db.get_cells([], ["CircularityFeature"]).empty


def test_delete_removes_cells_too(make_df):
    id_a = db.import_dataset("A", make_df(30))
    id_b = db.import_dataset("B", make_df(20))

    db.delete_datasets([id_a])

    assert db.list_datasets()["name"].tolist() == ["B"]
    with db.engine.connect() as conn:
        remaining = conn.execute(text("SELECT COUNT(*) FROM cells")).scalar()
        orphans = conn.execute(
            text("SELECT COUNT(*) FROM cells WHERE dataset_id = :i"), {"i": id_a}
        ).scalar()
    assert remaining == 20
    assert orphans == 0
    assert id_b in db.list_datasets()["id"].tolist()


def test_delete_nothing_is_noop(make_df):
    db.import_dataset("A", make_df())
    db.delete_datasets([])
    assert len(db.list_datasets()) == 1


def test_check_db():
    assert db.check_db() is True
