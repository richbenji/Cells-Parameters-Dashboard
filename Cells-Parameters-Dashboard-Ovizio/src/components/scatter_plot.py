import sqlite3
import pandas as pd
import plotly.express as px
from dash import dcc, html, Output, Input, callback

# Composant Dash pour le scatter plot
scatter_plot_component = html.Div([
    html.Label("Sélectionner l'axe X :"),
    dcc.Dropdown(id="x-axis", options=[], value=None, clearable=False),

    html.Label("Sélectionner l'axe Y :"),
    dcc.Dropdown(id="y-axis", options=[], value=None, clearable=False),

    dcc.Graph(id="scatter-plot")
])


# Fonction pour récupérer les colonnes des données
def get_column_options():
    conn = sqlite3.connect("cell_data.db")
    df = pd.read_sql("SELECT * FROM cells LIMIT 1", conn)
    conn.close()
    return [{"label": col, "value": col} for col in df.columns if col != "id"]


# Callback pour mettre à jour les dropdowns
@callback(
    Output("x-axis", "options"),
    Output("y-axis", "options"),
    Input("x-axis", "id")  # Juste pour déclencher le callback
)
def update_dropdowns(_):
    options = get_column_options()
    return options, options


# Callback pour afficher le scatter plot
@callback(
    Output("scatter-plot", "figure"),
    Input("x-axis", "value"),
    Input("y-axis", "value")
)
def update_scatter(x_col, y_col):
    if not x_col or not y_col:
        return px.scatter(title="Sélectionnez deux axes")

    conn = sqlite3.connect("cell_data.db")
    df = pd.read_sql("SELECT * FROM cells", conn)
    conn.close()

    fig = px.scatter(df, x=x_col, y=y_col, color="PhaseContrastFeature", title=f"{x_col} vs {y_col}")
    return fig