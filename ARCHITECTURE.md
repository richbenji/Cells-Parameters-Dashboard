# Architecture et fonctionnement du code

## Vue d'ensemble

L'application suit une séparation simple en couches. Chaque fichier a un rôle
unique et ne dépend que des couches situées « en dessous » :

```
main.py          point d'entrée : assemble l'application
  ├── layout.py       ce qui s'affiche (composants Dash)
  ├── callbacks.py    ce qui se passe quand l'utilisateur agit
  │     ├── plots.py            construction des graphiques
  │     ├── data_processing.py  lecture et validation des CSV
  │     └── database.py         tout le SQL
  └── config.py       constantes partagées (chemins, liste des colonnes)
```

Règle de conception : **le SQL n'existe que dans `database.py`**, la mise en
page que dans `layout.py`, et les figures que dans `plots.py`. Cela permet de
tester chaque partie séparément (voir `tests/`).

## Parcours des données

**Importer un CSV**
```
clic sur « Import CSV »
  → dcc.Upload envoie le fichier encodé en base64 au serveur
  → callbacks.update_datasets
  → data_processing.parse_upload      décode en octets
  → data_processing.load_csv          lit, valide, force le type numérique
  → database.import_dataset           insère le dataset et ses cellules (transaction)
  → le tableau est rechargé depuis la base
```

**Afficher un graphique**
```
changement de feature ou d'onglet
  → callbacks.update_scatter / update_histogram
  → plots.*_figure
  → database.get_cells                SELECT des colonnes demandées, tous datasets
  → Plotly construit la figure, une couleur par dataset
  → dcc.Graph l'affiche
```

## Fichier par fichier

### `config.py` : constantes partagées
Définit la racine du projet, le dossier de la base (`DATA_DIR`, modifiable par
variable d'environnement), l'URL SQLAlchemy et la liste `FEATURE_COLUMNS` des
26 colonnes attendues dans un CSV. Cette liste est la source unique de vérité :
elle sert à valider les CSV, à créer la table, à protéger les requêtes SQL et à
remplir les menus déroulants.
Le dossier de données est créé dès l'import du module, c'est pourquoi les tests
définissent `DATA_DIR` avant d'importer l'application.

### `data_processing.py` : de l'octet au DataFrame
- `read_csv_bytes` lit le CSV avec détection automatique du séparateur.
- `parse_upload` décode le texte `data:...;base64,...` fourni par `dcc.Upload`.
- `validate_dataframe` vérifie la présence des 26 colonnes (et liste celles qui
  manquent), convertit en nombres (valeur illisible → `NaN`) et refuse un fichier
  sans ligne. Les erreurs sont des `ValueError` au message lisible, affiché tel
  quel à l'utilisateur.
- `load_csv` enchaîne ces étapes ; le nom du dataset est le nom du fichier sans extension.
- `feature_label` / `feature_options` fabriquent les libellés des menus
  (`EquivalentCellDiameterFeature` → « Equivalent Cell Diameter »).

### `database.py` : tout le SQL
Deux tables :
- `datasets(id, name UNIQUE, cell_count, imported_at)`
- `cells(dataset_id → datasets.id ON DELETE CASCADE, 26 colonnes REAL)`

Points importants :
- **Clés étrangères.** SQLite ne les applique pas par défaut ; un écouteur
  d'événement active `PRAGMA foreign_keys = ON` à chaque connexion. Sans cela,
  la suppression en cascade ne fonctionnerait pas.
- **Transactions.** `engine.begin()` valide tout à la sortie du bloc ou annule tout en
  cas d'erreur. `import_dataset` insère le dataset et ses cellules dans la même
  transaction : l'import est « tout ou rien ».
- **Requêtes paramétrées.** Les valeurs ne sont jamais collées dans le SQL :
  elles passent par des paramètres liés (`:n`, `:ids`). Pour une liste
  (`IN :ids`), `expanding=True` génère le bon nombre de paramètres.
- **Liste blanche.** Un nom de colonne ne peut pas être un paramètre lié. `get_cells`
  vérifie donc chaque colonne demandée contre `FEATURE_COLUMNS` avant de
  l'écrire dans la requête : c'est la protection contre l'injection SQL.
- **`AUTOINCREMENT`.** Un id supprimé n'est jamais réutilisé, ce qui garde stable
  la couleur d'un dataset.
- `check_db` sert au health check.

### `plots.py` : les figures
- `_color_map` associe une couleur à chaque dataset d'après son id. La couleur
  ne change donc pas quand d'autres datasets sont ajoutés ou supprimés (la
  palette compte 10 couleurs, elle se répète au-delà).
- `scatter_figure(x, y)` trace un nuage de points avec `render_mode="webgl"`,
  nettement plus fluide que le rendu SVG pour des dizaines de milliers de points.
- `histogram_figure(feature)` superpose les histogrammes. Les classes (bins)
  sont calculées une seule fois sur l'ensemble des valeurs pour que les barres
  des différents datasets soient comparables.
- `empty_figure` affiche un message quand il n'y a aucune donnée.

### `layout.py` : la page
Ne contient que des composants, aucune logique. Chaque composant interactif a un
`id` (`upload`, `delete-btn`, `datasets-table`, `scatter-x`…) : ces identifiants
forment le contrat avec `callbacks.py`. La page est construite une fois au
démarrage ; le tableau part vide et se remplit au chargement.

### `callbacks.py` : les interactions
Dash appelle automatiquement une fonction de callback quand un de ses `Input`
change, puis place ses valeurs de retour dans les `Output` (dans le même ordre).
- `update_datasets` gère l'import, la suppression et le chargement initial. Il
  utilise `ctx.triggered_id` pour savoir qui l'a déclenché. Chaque fichier d'un
  import multiple est traité séparément : un CSV invalide n'empêche pas les
  autres. `selected_rows` contient des indices de lignes, et l'id réel du dataset
  est retrouvé dans les données du tableau.
- `update_scatter` et `update_histogram` recalculent leur figure quand la
  feature change ou quand on revient sur l'onglet Graphs. Ils ne font rien tant
  que cet onglet n'est pas actif.
- `no_update` signifie « ne modifie pas cette sortie ».

### `main.py` : l'assemblage
Crée les tables (`init_db`), construit l'application Dash, branche le layout et
les callbacks, expose `server` (l'objet Flask que gunicorn lance dans le
conteneur) et ajoute la route `/health`, qui répond 200 si la base est
joignable, sinon 503. Le bloc `if __name__ == "__main__"` ne s'exécute qu'en
lançant `python -m src.main`.

## Pourquoi `python -m src.main`

Les fichiers utilisent des imports relatifs (`from . import database`), qui ne
fonctionnent que si `src` est chargé comme un paquet. L'option `-m` exécute un
module par son nom d'import depuis la racine du projet. `python src/main.py`
chargerait `main.py` comme un script isolé et échouerait.

## Limites connues et pistes d'amélioration

- Les graphiques affichent **tous** les datasets ; on pourrait ajouter un choix
  des datasets à afficher.
- Chaque rafraîchissement relit les colonnes concernées en base et les envoie au
  navigateur ; au-delà de quelques centaines de milliers de points, il faudrait
  échantillonner ou agréger côté serveur.
- Le nom d'un dataset est celui du fichier : deux fichiers de même nom sont refusés.
- `dash_table.DataTable` est annoncé comme déprécié dans une future version
  majeure de Dash ; `dash-ag-grid` serait son remplaçant.
- `debug=True` est réservé au développement.
