"""Construction des figures Plotly (scatter plot et histogramme)."""
import plotly.express as px
import plotly.graph_objects as go

from . import database as db
from .data_processing import feature_label

PALETTE = px.colors.qualitative.Plotly
HISTOGRAM_BINS = 60


def _color_map() -> dict[str, str]:
    """Une couleur stable par dataset (basée sur son id : elle ne change pas
    quand on supprime ou ajoute d'autres datasets)."""
    datasets = db.list_datasets()
    return {row.name: PALETTE[row.id % len(PALETTE)]
            for row in datasets.itertuples()}


def _load(columns: list[str]):
    """Charge les cellules de TOUS les datasets pour les colonnes demandées."""
    ids = db.list_datasets()["id"].tolist()
    columns = list(dict.fromkeys(columns))  # dédoublonne (cas X == Y)
    return db.get_cells(ids, columns)


def empty_figure(message: str = "Aucun dataset importé") -> go.Figure:
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

    fig = px.scatter(
        df, x=x, y=y, color="dataset",
        color_discrete_map=_color_map(),
        labels={x: feature_label(x), y: feature_label(y), "dataset": "Dataset"},
        render_mode="webgl",   # fluide même avec des dizaines de milliers de points
    )
    fig.update_traces(marker={"size": 4, "opacity": 0.7})
    fig.update_layout(height=500, legend_title_text="")
    return fig


def histogram_figure(feature: str) -> go.Figure:
    df = _load([feature])
    values = df[feature].dropna()
    if values.empty:
        return empty_figure()

    fig = px.histogram(
        df, x=feature, color="dataset",
        barmode="overlay", opacity=0.6,
        color_discrete_map=_color_map(),
        labels={feature: feature_label(feature), "dataset": "Dataset"},
    )
    # Mêmes classes pour tous les datasets, sinon les barres ne sont pas comparables
    lo, hi = float(values.min()), float(values.max())
    size = (hi - lo) / HISTOGRAM_BINS or 1.0
    fig.update_traces(xbins={"start": lo, "end": hi, "size": size})
    fig.update_layout(height=450, legend_title_text="", yaxis_title="Count")
    return fig
