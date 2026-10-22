"""Point d'entrée de l'application.

Lancer depuis la racine du projet :
    python -m ovizio_app.main
"""
import dash_bootstrap_components as dbc
from dash import Dash
from flask import jsonify

from . import database as db
from .callbacks import register_callbacks
from .layout import build_layout

db.init_db()

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="Ovizio – Cell parameters",
)
app.layout = build_layout()
register_callbacks(app)

# Pour gunicorn (Docker) : gunicorn ovizio_app.main:server
server = app.server


@server.route("/health")
def health():
    """Health check : répond 200 si l'application et la base sont OK."""
    db_ok = db.check_db()
    body = {"status": "ok" if db_ok else "error",
            "database": "up" if db_ok else "down"}
    return jsonify(body), (200 if db_ok else 503)

if __name__ == "__main__":
    app.run(debug=True)
