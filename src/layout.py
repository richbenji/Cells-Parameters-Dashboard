"""Mise en page Dash (aucune logique ici, uniquement des composants).

Chaque composant interactif a un `id`. Ces identifiants sont le "contrat"
avec callbacks.py : un callback désigne les composants qu'il lit (Input,
State) et qu'il modifie (Output) par leur id. Renommer un id ici impose de
le renommer là-bas.
"""
import dash_bootstrap_components as dbc
from dash import dash_table, dcc, html

from .config import DEFAULT_X, DEFAULT_Y
from .data_processing import feature_options


def datasets_tab() -> html.Div:
    # Tableau des datasets. Il est créé vide (data=[]) : c'est le callback
    # update_datasets qui le remplit au chargement de la page.
    table = dash_table.DataTable(
        id="datasets-table",
        columns=[
            {"name": "Name", "id": "name"},
            {"name": "Cell Count", "id": "cell_count", "type": "numeric"},
        ],
        data=[],
        row_selectable="multi",   # cases à cocher, comme dans la maquette
        selected_rows=[],          # liste des indices de lignes cochées
        style_header={"fontWeight": "bold"},
        style_cell={"textAlign": "left", "padding": "6px"},
        style_cell_conditional=[
            {"if": {"column_id": "cell_count"}, "width": "160px"}
        ],
    )

    # dcc.Upload rend cliquable tout ce qu'on met dans "children" : ici, un bouton.
    # multiple=True : on peut choisir plusieurs fichiers, et le callback reçoit
    # alors des LISTES (contents et filename).
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
        # Classes Bootstrap : flex = éléments côte à côte, between = un à chaque
        # bord, mt-3 = marge en haut.
        className="d-flex justify-content-between mt-3",
    )

    # Zone de message : cachée au départ (is_open=False). Le callback change son
    # texte, sa couleur et son état ouvert/fermé pour signaler succès ou erreurs.
    return html.Div(
        [
            dbc.Alert(id="message", is_open=False, dismissable=True,
                      className="mt-3"),
            html.Div(table, className="mt-3"),
            buttons,
        ]
    )


def _feature_dropdown(component_id: str, value: str) -> dcc.Dropdown:
    # Menu déroulant de features, réutilisé trois fois (X, Y, histogramme).
    # clearable=False : on ne peut pas le vider, il y a toujours une feature choisie.
    return dcc.Dropdown(
        id=component_id,
        options=feature_options(),
        value=value,
        clearable=False,
    )


def graphs_tab() -> html.Div:
    # Les dcc.Graph sont créés sans figure : elles sont remplies par les
    # callbacks update_scatter et update_histogram.
    # dbc.Row / dbc.Col : grille Bootstrap sur 12 colonnes (label sur 2, menu sur 5).
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
    # Assemble la page : titre + deux onglets. Les contenus des onglets sont
    # tous construits au démarrage et présents dans la page ; seul l'onglet
    # actif est visible. C'est pour ça que les graphiques ne sont recalculés
    # que lorsque l'onglet Graphs est actif (voir callbacks.py).
    # Cette fonction n'est appelée qu'une fois, au démarrage du serveur.
    return dbc.Container(
        [
            html.H2("Cell parameters", className="my-3"),
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
