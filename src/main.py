"""Point d'entrée de l'application.

Lancer depuis la racine du projet :
    python -m src.main
"""
import dash_bootstrap_components as dbc
from dash import Dash
from flask import jsonify

from . import database as db
from .callbacks import register_callbacks
from .layout import build_layout

# Crée les tables au démarrage si elles n'existent pas. Cette ligne s'exécute
# à l'import du module, donc aussi quand gunicorn charge l'application.
# Elle peut être exécutée par plusieurs workers sans risque (CREATE ... IF NOT EXISTS).
db.init_db()

# Dash est construit au-dessus de Flask. __name__ ("src.main") permet à Dash de
# repérer le dossier du projet (par exemple pour un éventuel dossier assets/).
# dbc.themes.BOOTSTRAP : feuille de style Bootstrap pour les composants dbc.
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="Cell parameters",
)
app.layout = build_layout()    # la page (voir layout.py)
register_callbacks(app)        # les interactions (voir callbacks.py)

# Le serveur Flask sous-jacent. C'est cet objet que gunicorn lance dans le
# conteneur : gunicorn src.main:server
server = app.server


# Dash étant construit sur Flask, on peut y ajouter des routes ordinaires.
@server.route("/health")
def health():
    """Health check : répond 200 si l'application et la base sont OK."""
    db_ok = db.check_db()
    body = {"status": "ok" if db_ok else "error",
            "database": "up" if db_ok else "down"}
    # 200 = tout va bien ; 503 = service indisponible. Podman/Docker se basent
    # sur ce code pour marquer le conteneur "healthy" ou "unhealthy".
    return jsonify(body), (200 if db_ok else 503)


# Ce bloc ne s'exécute que lorsqu'on lance "python -m src.main" (développement).
# Avec gunicorn, le module est importé et ce bloc est ignoré.
# debug=True : rechargement automatique du code et erreurs détaillées dans le
# navigateur. Ne jamais l'activer en production.
if __name__ == "__main__":
    app.run(debug=True)
