import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import io
from database import insert_dataset, get_datasets

upload_component = dbc.Card([
    html.H5("Importer un dataset"),
    dcc.Upload(
        id="upload-data",
        children=html.Button("Choisir un fichier"),
        multiple=False
    ),
    html.Div(id="upload-status", style={"marginTop": "10px"})
])

def register_upload_callbacks(app):
    @app.callback(
        Output("upload-status", "children"),
        Output("dataset-list", "options"),
        Input("upload-data", "contents"),
        State("upload-data", "filename"),
        prevent_initial_call=True
    )
    def upload_csv(contents, filename):
        if not contents:
            return "Aucun fichier sélectionné", dash.no_update

        # Convertir le contenu base64 en DataFrame Pandas
        content_type, content_string = contents.split(",")
        decoded = io.StringIO(content_string)
        df = pd.read_csv(decoded)

        # Insérer dans la base de données
        insert_dataset(filename, df)

        # Mettre à jour la liste des datasets
        datasets = get_datasets()
        options = [{"label": f"{d[1]}", "value": d[0]} for d in datasets]

        return f"Fichier {filename} importé avec succès", options
