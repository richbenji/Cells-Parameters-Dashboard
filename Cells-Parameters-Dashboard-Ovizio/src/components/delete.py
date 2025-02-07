import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
from database import get_datasets, delete_datasets

delete_component = dbc.Card([
    html.H5("Supprimer un dataset"),
    html.Div(id="dataset-list"),
    dbc.Button("Supprimer", id="delete-btn", color="danger", style={"marginTop": "10px"})
])


def register_delete_callbacks(app):
    @app.callback(
        Output("dataset-list", "children"),
        Input("delete-btn", "n_clicks"),
        Input("dataset-list", "value"),
        prevent_initial_call=True
    )
    def update_or_delete(n_clicks, selected_ids):
        if dash.callback_context.triggered_id == "delete-btn":
            if not selected_ids:
                return "Aucun fichier sélectionné."
            delete_datasets(selected_ids)  # Suppression en base de données

        # Met à jour la liste des datasets après suppression
        datasets = get_datasets()
        return dcc.Checklist(
            options=[{"label": f"{d[1]}", "value": d[0]} for d in datasets],
            id="dataset-list",
            inline=True
        )
