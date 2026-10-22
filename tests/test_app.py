from ovizio_app import plots
from ovizio_app.main import server


def test_health_endpoint():
    response = server.test_client().get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "database": "up"}


def test_figures_with_no_data():
    # Aucun dataset : on doit obtenir une figure vide, pas une exception
    assert len(plots.scatter_figure("CircularityFeature", "CellAreaFeature").data) == 0
    assert len(plots.histogram_figure("CircularityFeature").data) == 0


def test_one_trace_per_dataset(make_df):
    from ovizio_app import database as db
    db.import_dataset("A", make_df(20, seed=1))
    db.import_dataset("B", make_df(20, seed=2))

    scatter = plots.scatter_figure("EquivalentCellDiameterFeature", "CircularityFeature")
    hist = plots.histogram_figure("EquivalentCellDiameterFeature")

    assert {t.name for t in scatter.data} == {"A", "B"}
    assert {t.name for t in hist.data} == {"A", "B"}
    # une couleur distincte par dataset
    assert len({t.marker.color for t in scatter.data}) == 2


def test_scatter_same_feature_on_both_axes(make_df):
    from ovizio_app import database as db
    db.import_dataset("A", make_df(20))
    fig = plots.scatter_figure("CircularityFeature", "CircularityFeature")
    assert len(fig.data) == 1
