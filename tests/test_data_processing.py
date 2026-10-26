"""Tests de la lecture et de la validation des CSV (src/data_processing.py).

Ces tests n'utilisent pas la base : ils vérifient seulement la transformation
de CSV en DataFrame.
"""
import pytest

from src.config import FEATURE_COLUMNS
from src.data_processing import (feature_label, feature_options,
                                 load_csv, validate_dataframe)


def test_load_csv_comma(make_df):
    # On fabrique un vrai CSV en mémoire puis on l'encode en octets, comme le
    # ferait l'upload. On vérifie le nom du dataset, le nombre de lignes et que
    # les colonnes sont celles attendues, dans l'ordre.
    content = make_df(10).to_csv(index=False).encode()
    name, df = load_csv("Donor-A-activated.csv", content)
    assert name == "Donor-A-activated"   # nom du fichier sans ".csv"
    assert len(df) == 10
    assert list(df.columns) == FEATURE_COLUMNS


def test_load_csv_semicolon(make_df):
    # Même chose avec ";" comme séparateur : la détection automatique doit le gérer.
    content = make_df(10).to_csv(index=False, sep=";").encode()
    _, df = load_csv("x.csv", content)
    assert len(df) == 10


def test_missing_columns_message(make_df):
    # Une colonne retirée : l'erreur doit nommer la colonne manquante, pour que
    # l'utilisateur sache quoi corriger. "match" est une recherche dans le message.
    df = make_df(5).drop(columns=["CircularityFeature"])
    with pytest.raises(ValueError, match="CircularityFeature"):
        validate_dataframe(df)


def test_empty_file_rejected(make_df):
    # En-têtes présents mais zéro ligne : ce n'est pas un dataset utilisable.
    with pytest.raises(ValueError, match="aucune cellule"):
        validate_dataframe(make_df(0))


def test_non_numeric_values_become_nan(make_df):
    # astype(object) permet de mettre du texte dans une colonne de nombres.
    # La valeur illisible doit devenir NaN, sans faire échouer tout l'import.
    df = make_df(3).astype(object)
    df.loc[0, "CircularityFeature"] = "abc"
    out = validate_dataframe(df)
    assert out["CircularityFeature"].isna().sum() == 1


def test_feature_label():
    # CamelCase → mots séparés, suffixe "Feature" retiré ; "Time [h]" inchangé.
    assert feature_label("EquivalentCellDiameterFeature") == "Equivalent Cell Diameter"
    assert feature_label("Time [h]") == "Time [h]"


def test_feature_options_cover_all_columns():
    # Les menus déroulants doivent proposer exactement les 26 colonnes, dans l'ordre.
    values = [o["value"] for o in feature_options()]
    assert values == FEATURE_COLUMNS
