import pytest

from ovizio_app.data_processing import (feature_label, feature_options,
                                        load_csv, validate_dataframe)
from ovizio_app.config import FEATURE_COLUMNS


def test_load_csv_comma(make_df):
    content = make_df(10).to_csv(index=False).encode()
    name, df = load_csv("Donor-A-activated.csv", content)
    assert name == "Donor-A-activated"
    assert len(df) == 10
    assert list(df.columns) == FEATURE_COLUMNS


def test_load_csv_semicolon(make_df):
    content = make_df(10).to_csv(index=False, sep=";").encode()
    _, df = load_csv("x.csv", content)
    assert len(df) == 10


def test_missing_columns_message(make_df):
    df = make_df(5).drop(columns=["CircularityFeature"])
    with pytest.raises(ValueError, match="CircularityFeature"):
        validate_dataframe(df)


def test_empty_file_rejected(make_df):
    with pytest.raises(ValueError, match="aucune cellule"):
        validate_dataframe(make_df(0))


def test_non_numeric_values_become_nan(make_df):
    df = make_df(3).astype(object)
    df.loc[0, "CircularityFeature"] = "abc"
    out = validate_dataframe(df)
    assert out["CircularityFeature"].isna().sum() == 1


def test_feature_label():
    assert feature_label("EquivalentCellDiameterFeature") == "Equivalent Cell Diameter"
    assert feature_label("Time [h]") == "Time [h]"


def test_feature_options_cover_all_columns():
    values = [o["value"] for o in feature_options()]
    assert values == FEATURE_COLUMNS
