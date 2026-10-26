"""Tests de l'application : health check et figures (src/main.py, src/plots.py).

Importer src.main construit toute l'application (layout et callbacks compris) :
si l'un d'eux est cassé, ces tests échouent dès l'import.
"""
from src import plots
from src.main import server


def test_health_endpoint():
    # test_client() de Flask appelle la route directement, sans lancer de
    # serveur ni ouvrir de port.
    response = server.test_client().get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "database": "up"}


def test_figures_with_no_data():
    # Aucun dataset : on doit obtenir une figure vide (0 série), pas une exception.
    assert len(plots.scatter_figure("CircularityFeature", "CellAreaFeature").data) == 0
    assert len(plots.histogram_figure("CircularityFeature").data) == 0


def test_one_trace_per_dataset(make_df):
    # L'import est local à la fonction ; on pourrait aussi le mettre en haut du fichier.
    from src import database as db
    db.import_dataset("A", make_df(20, seed=1))
    db.import_dataset("B", make_df(20, seed=2))

    scatter = plots.scatter_figure("EquivalentCellDiameterFeature", "CircularityFeature")
    hist = plots.histogram_figure("EquivalentCellDiameterFeature")

    # Une série (trace) par dataset, nommée d'après le dataset : c'est ce qui
    # produit une couleur et une entrée de légende par dataset.
    assert {t.name for t in scatter.data} == {"A", "B"}
    assert {t.name for t in hist.data} == {"A", "B"}
    # une couleur distincte par dataset
    assert len({t.marker.color for t in scatter.data}) == 2


def test_scatter_same_feature_on_both_axes(make_df):
    # X == Y : la même colonne n'est lue qu'une fois, et le graphique se construit.
    from src import database as db
    db.import_dataset("A", make_df(20))
    fig = plots.scatter_figure("CircularityFeature", "CircularityFeature")
    assert len(fig.data) == 1
