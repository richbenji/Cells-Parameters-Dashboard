"""Callbacks Dash : relient l'interface à la base de données.

Un callback est une fonction que Dash appelle automatiquement quand un
composant change :
  - Input  : ce qui déclenche l'appel (clic, choix dans un menu, fichier…) ;
  - State  : valeurs lues au moment de l'appel, sans le déclencher ;
  - Output : composants mis à jour avec ce que la fonction retourne.
Les valeurs retournées doivent être dans le même ordre que les Output.
"""
from dash import Input, Output, State, ctx, no_update

from . import database as db
from . import plots
from .data_processing import load_csv, parse_upload


def _table_rows() -> list[dict]:
    # Transforme la liste des datasets en lignes pour le DataTable :
    # [{"id": 1, "name": "...", "cell_count": 6989}, ...].
    # L'id n'est pas affiché (il n'est pas dans "columns"), mais reste dans les
    # données : c'est lui qui sert à la suppression.
    return db.list_datasets()[["id", "name", "cell_count"]].to_dict("records")


def register_callbacks(app) -> None:
    # Les callbacks sont déclarés dans une fonction qui reçoit l'app, plutôt
    # que dans le module : main.py peut ainsi créer l'app d'abord, puis brancher
    # les callbacks dessus.

    # ------------------------------------------------------------------
    # Onglet Datasets : import et suppression partagent un seul callback,
    # car les deux modifient les mêmes composants (tableau et message).
    # ------------------------------------------------------------------
    @app.callback(
        Output("datasets-table", "data"),
        Output("datasets-table", "selected_rows"),
        Output("message", "children"),
        Output("message", "color"),
        Output("message", "is_open"),
        Input("upload", "contents"),
        Input("delete-btn", "n_clicks"),
        State("upload", "filename"),
        State("datasets-table", "selected_rows"),
        State("datasets-table", "data"),
    )
    def update_datasets(contents, _n_clicks, filenames, selected_rows, rows):
        # ctx.triggered_id : l'id du composant qui a déclenché l'appel
        # (None au chargement initial de la page).
        trigger = ctx.triggered_id

        # --- Import de un ou plusieurs CSV -------------------------------
        if trigger == "upload" and contents:
            ok, errors = [], []
            # Avec multiple=True, "contents" et "filename" sont deux listes
            # parallèles : on les parcourt ensemble avec zip.
            for content, filename in zip(contents, filenames):
                # Chaque fichier est traité séparément : un CSV invalide
                # n'empêche pas l'import des autres.
                try:
                    name, df = load_csv(filename, parse_upload(content))
                    db.import_dataset(name, df)
                    ok.append(f"{name} ({len(df)} cellules)")
                except Exception as exc:  # message lisible pour l'utilisateur
                    errors.append(f"{filename} : {exc}")

            # Choix du message : tout est passé (vert), tout a échoué (rouge)
            # ou résultat mixte (orange).
            if errors:
                msg = "Erreur d'import — " + " | ".join(errors)
                if ok:
                    msg = "Importé : " + ", ".join(ok) + ". " + msg
                color = "warning" if ok else "danger"
            else:
                msg, color = "Importé : " + ", ".join(ok), "success"
            # [] : on décoche les lignes, les indices ne sont plus valables.
            return _table_rows(), [], msg, color, True

        # --- Suppression des datasets cochés -----------------------------
        if trigger == "delete-btn":
            if not selected_rows:
                # no_update : laisse le tableau tel quel, affiche seulement le message.
                return no_update, no_update, "Aucun dataset sélectionné.", "info", True
            # selected_rows contient des indices de lignes (0, 1, 2…) et non des ids
            # de base : on retrouve l'id réel dans les données du tableau.
            ids = [rows[i]["id"] for i in selected_rows]
            db.delete_datasets(ids)
            return (_table_rows(), [],
                    f"{len(ids)} dataset(s) supprimé(s).", "success", True)

        # --- Chargement initial de la page -------------------------------
        # Aucun déclencheur : on remplit le tableau avec ce qui est en base
        # et on garde le message caché.
        return _table_rows(), [], "", "info", False

    # ------------------------------------------------------------------
    # Graphiques : rafraîchis quand on change de feature OU quand on
    # revient sur l'onglet Graphs (les datasets ont pu changer entre-temps).
    # ------------------------------------------------------------------
    @app.callback(
        Output("scatter-graph", "figure"),
        Input("tabs", "active_tab"),
        Input("scatter-x", "value"),
        Input("scatter-y", "value"),
    )
    def update_scatter(active_tab, x, y):
        # Tant que l'onglet Graphs n'est pas affiché, on ne calcule rien
        # (inutile, et un graphique tracé dans un onglet caché a une taille nulle).
        if active_tab != "tab-graphs":
            return no_update
        return plots.scatter_figure(x, y)

    @app.callback(
        Output("hist-graph", "figure"),
        Input("tabs", "active_tab"),
        Input("hist-feature", "value"),
    )
    def update_histogram(active_tab, feature):
        if active_tab != "tab-graphs":
            return no_update
        return plots.histogram_figure(feature)
