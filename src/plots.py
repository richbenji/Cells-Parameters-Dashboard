"""Construction des figures Plotly (scatter plot et histogramme).

Ce module lit la base, construit une figure et la retourne. Il ne connaît
pas Dash : c'est callbacks.py qui l'appelle et affiche le résultat.
"""
import plotly.express as px
import plotly.graph_objects as go

from . import database as db
from .data_processing import feature_label

# Palette de 10 couleurs fournie par Plotly.
PALETTE = px.colors.qualitative.Plotly
# Nombre de classes (barres) de l'histogramme.
HISTOGRAM_BINS = 60


def _color_map() -> dict[str, str]:
    """Une couleur stable par dataset (basée sur son id : elle ne change pas
    quand on supprime ou ajoute d'autres datasets)."""
    datasets = db.list_datasets()
    # Dictionnaire {nom du dataset: couleur}. Le "%" fait boucler la palette :
    # au-delà de 10 datasets, les couleurs se répètent.
    return {row.name: PALETTE[row.id % len(PALETTE)]
            for row in datasets.itertuples()}


def _load(columns: list[str]):
    """Charge les cellules de TOUS les datasets pour les colonnes demandées."""
    ids = db.list_datasets()["id"].tolist()
    # dict.fromkeys garde l'ordre et supprime les doublons : si X et Y sont la
    # même feature, on ne demande la colonne qu'une fois à la base.
    columns = list(dict.fromkeys(columns))
    return db.get_cells(ids, columns)


def empty_figure(message: str = "Aucun dataset importé") -> go.Figure:
    # Figure vide avec un message centré, affichée quand il n'y a rien à tracer.
    fig = go.Figure()
    fig.add_annotation(text=message, showarrow=False, font={"size": 16})
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(height=450)
    return fig


def scatter_figure(x: str, y: str) -> go.Figure:
    df = _load([x, y])
    if df.empty:
        return empty_figure()

    # color="dataset" : Plotly crée une série (une couleur, une entrée de légende)
    # par valeur de cette colonne. color_discrete_map impose quelle couleur
    # va à quel dataset. "labels" remplace les noms de colonnes affichés.
    fig = px.scatter(
        df, x=x, y=y, color="dataset",
        color_discrete_map=_color_map(),
        labels={x: feature_label(x), y: feature_label(y), "dataset": "Dataset"},
        render_mode="webgl",   # fluide même avec des dizaines de milliers de points
    )
    # Petits points semi-transparents : on voit mieux les zones denses.
    fig.update_traces(marker={"size": 4, "opacity": 0.7})
    fig.update_layout(height=500, legend_title_text="")
    return fig


def histogram_figure(feature: str) -> go.Figure:
    df = _load([feature])
    values = df[feature].dropna()
    if values.empty:
        return empty_figure()

    # barmode="overlay" : les histogrammes se superposent (comme dans la
    # maquette) au lieu d'être côte à côte ; opacity permet de voir à travers.
    fig = px.histogram(
        df, x=feature, color="dataset",
        barmode="overlay", opacity=0.6,
        color_discrete_map=_color_map(),
        labels={feature: feature_label(feature), "dataset": "Dataset"},
    )
    # Mêmes classes pour tous les datasets, sinon les barres ne sont pas comparables
    # (par défaut, Plotly calcule des classes différentes pour chaque série).
    lo, hi = float(values.min()), float(values.max())
    # "or 1.0" : si toutes les valeurs sont identiques (hi == lo), la taille
    # serait 0, ce qui est impossible ; on prend alors 1.
    size = (hi - lo) / HISTOGRAM_BINS or 1.0
    fig.update_traces(xbins={"start": lo, "end": hi, "size": size})
    fig.update_layout(height=450, legend_title_text="", yaxis_title="Count")
    return fig
