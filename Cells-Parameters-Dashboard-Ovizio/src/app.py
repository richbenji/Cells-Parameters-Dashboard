import sqlite3
import dash
from dash import dcc, html
from database import init_db, insert_dataset, get_datasets, get_dataset_data, delete_dataset
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import pandas as pd
import os
import base64
import io

# Initialiser la base de données
init_db()

# Création de l'application Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    html.H1("Dashboard de Gestion de Datasets"),
    dcc.Upload(
        id='upload-data',
        children=html.Button("Importer un fichier CSV"),
        multiple=False
    ),
    html.Br(),
    html.H3("Fichiers disponibles :"),
    dcc.Dropdown(id='dataset-list', placeholder="Sélectionner un fichier"),
    html.Button("Supprimer", id='delete-btn', n_clicks=0),
    html.Div(id='output-msg'),
    html.Br(),
    html.Button("Afficher les données", id='show-data-btn', n_clicks=0),
    html.Div(id='data-table')
])

@app.callback(
    Output('dataset-list', 'options'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def upload_file(contents, filename):
    if contents is not None and filename:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        insert_dataset(filename, df)
    datasets = get_datasets()
    return [{'label': f, 'value': f} for _, f in datasets]

@app.callback(
    Output('output-msg', 'children'),
    Input('delete-btn', 'n_clicks'),
    State('dataset-list', 'value')
)
def delete_file(n_clicks, filename):
    if n_clicks > 0 and filename:
        datasets = get_datasets()
        dataset_id = next((id for id, f in datasets if f == filename), None)
        if dataset_id:
            delete_dataset(dataset_id, filename)
            return "Fichier supprimé avec succès!"
    return ""

@app.callback(
    Output('data-table', 'children'),
    Input('show-data-btn', 'n_clicks'),
    State('dataset-list', 'value')
)
def show_data(n_clicks, filename):
    if n_clicks > 0 and filename:
        df = get_dataset_data(filename)
        return html.Table([
            html.Thead([html.Tr([html.Th(col) for col in df.columns])]),
            html.Tbody([
                html.Tr([html.Td(df.iloc[i][col]) for col in df.columns]) for i in range(min(len(df), 10))
            ])
        ])
    return ""

if __name__ == "__main__":
    app.run_server(debug=True)
