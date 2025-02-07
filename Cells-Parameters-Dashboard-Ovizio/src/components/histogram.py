import sqlite3
import pandas as pd
import plotly.express as px
from dash import dcc, html, Output, Input, callback

# Composant Dash pour l'histogramme
histogram_component = html.Div([
    html.Label("Sélectionner une colonne :"),
    dcc.Dropdown(id="histogram-column", options=[], value=None, clearable=False),

    dcc.Graph(id="histogram")
])

# Fonction pour récupérer les colonnes des données
def get_column_options():
    conn = sqlite3.connect("cell_data.db")
    df = pd.read_sql("SELECT * FROM cells LIMIT 1", conn)
    conn.close()
    return [{"label": col, "value": col} for col in df.columns if col != "id"]

# Callback pour mettre à jour le dropdown
@callback(
    Output("histogram-column", "options"),
    Input("histogram-column", "id")  # Juste pour déclencher le callback
)
def update_dropdown(_):
    return get_column_options()

# Callback pour afficher l'histogramme
@callback(
    Output("histogram", "figure"),
    Input("histogram-column", "value")
)
def update_histogram(column):
    if not column:
        return px.histogram(title="Sélectionnez une colonne")

    conn = sqlite3.connect("cell_data.db")
    df = pd.read_sql("SELECT * FROM cells", conn)
    conn.close()

    fig = px.histogram(df, x=column, title=f"Distribution de {column}")
    return fig