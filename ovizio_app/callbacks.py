"""Callbacks Dash : relient l'interface à la base de données."""
from dash import Input, Output, State, ctx, no_update

from . import database as db
from . import plots
from .data_processing import load_csv, parse_upload


def _table_rows() -> list[dict]:
    return db.list_datasets()[["id", "name", "cell_count"]].to_dict("records")


def register_callbacks(app) -> None:

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
        trigger = ctx.triggered_id

        # --- Import de un ou plusieurs CSV -------------------------------
        if trigger == "upload" and contents:
            ok, errors = [], []
            for content, filename in zip(contents, filenames):
                try:
                    name, df = load_csv(filename, parse_upload(content))
                    db.import_dataset(name, df)
                    ok.append(f"{name} ({len(df)} cellules)")
                except Exception as exc:  # message lisible pour l'utilisateur
                    errors.append(f"{filename} : {exc}")

            if errors:
                msg = "Erreur d'import — " + " | ".join(errors)
                if ok:
                    msg = "Importé : " + ", ".join(ok) + ". " + msg
                color = "warning" if ok else "danger"
            else:
                msg, color = "Importé : " + ", ".join(ok), "success"
            return _table_rows(), [], msg, color, True

        # --- Suppression des datasets cochés -----------------------------
        if trigger == "delete-btn":
            if not selected_rows:
                return no_update, no_update, "Aucun dataset sélectionné.", "info", True
            ids = [rows[i]["id"] for i in selected_rows]
            db.delete_datasets(ids)
            return (_table_rows(), [],
                    f"{len(ids)} dataset(s) supprimé(s).", "success", True)

        # --- Chargement initial de la page -------------------------------
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
