"""Mise en page Dash (aucune logique ici, uniquement des composants)."""
import dash_bootstrap_components as dbc
from dash import dash_table, dcc, html

from .config import DEFAULT_X, DEFAULT_Y
from .data_processing import feature_options


def datasets_tab() -> html.Div:
    table = dash_table.DataTable(
        id="datasets-table",
        columns=[
            {"name": "Name", "id": "name"},
            {"name": "Cell Count", "id": "cell_count", "type": "numeric"},
        ],
        data=[],
        row_selectable="multi",   # cases à cocher, comme dans la maquette
        selected_rows=[],
        style_header={"fontWeight": "bold"},
        style_cell={"textAlign": "left", "padding": "6px"},
        style_cell_conditional=[
            {"if": {"column_id": "cell_count"}, "width": "160px"}
        ],
    )

    buttons = html.Div(
        [
            dcc.Upload(
                id="upload",
                children=dbc.Button("Import CSV", color="secondary"),
                multiple=True,          # plusieurs CSV d'un coup
                accept=".csv",
            ),
            dbc.Button("Delete Selected", id="delete-btn", color="danger",
                       outline=True),
        ],
        className="d-flex justify-content-between mt-3",
    )

    return html.Div(
        [
            dbc.Alert(id="message", is_open=False, dismissable=True,
                      className="mt-3"),
            html.Div(table, className="mt-3"),
            buttons,
        ]
    )


def _feature_dropdown(component_id: str, value: str) -> dcc.Dropdown:
    return dcc.Dropdown(
        id=component_id,
        options=feature_options(),
        value=value,
        clearable=False,
    )


def graphs_tab() -> html.Div:
    return html.Div(
        [
            html.H4("Plot X/Y", className="mt-3"),
            dbc.Row(
                [
                    dbc.Col(html.Label("Feature X:"), width=2),
                    dbc.Col(_feature_dropdown("scatter-x", DEFAULT_X), width=5),
                ],
                className="mb-2 align-items-center",
            ),
            dbc.Row(
                [
                    dbc.Col(html.Label("Feature Y:"), width=2),
                    dbc.Col(_feature_dropdown("scatter-y", DEFAULT_Y), width=5),
                ],
                className="mb-2 align-items-center",
            ),
            dcc.Graph(id="scatter-graph"),

            html.H4("Histogram", className="mt-4"),
            dbc.Row(
                [
                    dbc.Col(html.Label("Feature:"), width=2),
                    dbc.Col(_feature_dropdown("hist-feature", DEFAULT_X), width=5),
                ],
                className="mb-2 align-items-center",
            ),
            dcc.Graph(id="hist-graph"),
        ],
    )


def build_layout() -> dbc.Container:
    return dbc.Container(
        [
            html.H2("Ovizio – Cell parameters", className="my-3"),
            dbc.Tabs(
                [
                    dbc.Tab(datasets_tab(), label="Datasets", tab_id="tab-datasets"),
                    dbc.Tab(graphs_tab(), label="Graphs", tab_id="tab-graphs"),
                ],
                id="tabs",
                active_tab="tab-datasets",
            ),
        ],
        fluid=False,
    )
