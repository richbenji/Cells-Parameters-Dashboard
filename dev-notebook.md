# Cell parameters dashboard

# Étapes de développement du projet

## Initialisation du projet

On est dans : `/media/richard/PROGRAMMATION/Projets/ovizio`

### Création de l'environnement virtuel Python

```bash
# Créer un environnement virtuel dans un dossier appelé 'venv'
python3 -m venv venv

# Activer l'environnement virtuel
source venv/bin/activate  # Sur Linux/Mac

# Installer les dépendances
pip install -r requirements.txt

# Ou :
pip install dash pandas plotly sqlalchemy

# Actualiser le fichier requirements.txt
pip freeze > requirements.txt
```

### Dans PyCharm

`File` > `New File`=> Sélectionner le dossier `/media/richard/PROGRAMMATION/Projets/ovizio` . Interpréteur type : choisir `Custom environment`, générer un nouvel environnement et sélectionner dans `location`: `/media/richard/PROGRAMMATION/Projets/ovizio/venv` .

## **Création de la base de données (SQLite)**

Dans `database.py`, crée une base pour stocker les données des CSV :

```python
import sqlite3

DB_NAME = "cell_data.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            file_path TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Base de données initialisée.")
```

Lance ce fichier une fois pour créer la base :

```bash
python database.py
```

##  **Créer l'application Dash**

Dans `app.py`, crée une base pour l'application :

```python
import dash
from dash import html, dcc

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Dashboard Ovizio"),
    html.P("Importez vos fichiers CSV pour visualiser les paramètres des cellules."),
    dcc.Upload(id='upload-data', children=html.Button("Importer un fichier")),
    dcc.Graph(id="scatter-plot"),
    dcc.Graph(id="histogram")
])

if __name__ == "__main__":
    app.run_server(debug=True)
```

Lance l'application :

```bash
python app.py
```

## **Créer le module d'importation (`upload.py`)**

Crée un fichier `components/upload.py` et ajoute ce code :

```python
import os
import pandas as pd
import sqlite3
from dash import dcc, html, Output, Input, State, callback
import dash

# Dossier pour stocker les fichiers
UPLOAD_FOLDER = "data"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Composant Dash pour l'upload
upload_component = html.Div([
    dcc.Upload(
        id='upload-data',
        children=html.Button("Importer un fichier"),
        multiple=False
    ),
    html.Div(id='upload-status'),
])

# Fonction pour stocker le fichier et l'ajouter en base
def save_file(contents, filename):
    content_type, content_string = contents.split(',')
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    
    with open(file_path, "wb") as f:
        import base64
        f.write(base64.b64decode(content_string))

    return file_path

# Callback pour gérer l'importation
@callback(
    Output('upload-status', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def upload_file(contents, filename):
    if contents is None:
        return ""
    
    # Sauvegarde du fichier
    file_path = save_file(contents, filename)
    
    # Lire le CSV avec Pandas
    df = pd.read_csv(file_path)
    
    # Enregistrer les données dans SQLite
    conn = sqlite3.connect("cell_data.db")
    df.to_sql(name="cells", con=conn, if_exists="append", index=False)
    conn.close()
    
    return f"Le fichier {filename} a été importé et ajouté à la base de données."
```

## **Ajouter l'upload à `app.py`**

Modifie `app.py` pour inclure le module d'importation :

```python
import dash
from dash import html, dcc
from src.components.upload import upload_component

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Dashboard Ovizio"),
    upload_component,  # Ajout du composant upload
    dcc.Graph(id="scatter-plot"),
    dcc.Graph(id="histogram")
])

if __name__ == "__main__":
    app.run_server(debug=True)
```

## **Tester l'application**

Lance ton application avec :

```bash
python app.py
```

Ensuite :

1. Ouvre **http://127.0.0.1:8050/** dans ton navigateur.
2. Clique sur **Importer un fichier** et choisis un CSV.
3. Vérifie le message de confirmation d'importation.
4. Ouvre SQLite pour voir si les données sont bien stockées.

### Pour ouvrir SQLite et vérifier si les données ont bien été enregistrées :

#### **Utiliser le terminal avec `sqlite3`**

Si `sqlite3` est installé sur ton système, ouvre un terminal dans ton dossier de projet et tape :

```bash
sqlite3 cell_data.db
```

Puis, dans l'interface SQLite, exécute :

```sql
.tables  -- Pour voir les tables existantes
SELECT * FROM cells LIMIT 5;  -- Pour afficher les 5 premières lignes
```

Pour quitter SQLite, tape `.exit`.

------

#### **Utiliser Python pour lire la base**

Si tu préfères vérifier avec Python, crée un petit script `check_db.py` :

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect("cell_data.db")
df = pd.read_sql("SELECT * FROM cells LIMIT 5", conn)
conn.close()

print(df)
```

Exécute-le avec :

```bash
python check_db.py
```

------

#### **Utiliser un outil graphique (SQLite Browser)**

Si tu veux une interface visuelle, télécharge **DB Browser for SQLite** :
👉 https://sqlitebrowser.org/dl/

1. **Installe** l'outil.
2. **Ouvre** `cell_data.db` avec **DB Browser for SQLite**.
3. **Clique sur l'onglet "Browse Data"** pour voir tes données.

------

#### **Conclusion**

- **Méthode rapide** ➝ Terminal avec `sqlite3`.
- **Méthode facile** ➝ Petit script Python.
- **Méthode visuelle** ➝ DB Browser for SQLite.

## **Créer le module du scatter plot (`scatter_plot.py`)**

Crée un fichier `components/scatter_plot.py` et ajoute ce code :

```python
import sqlite3
import pandas as pd
import plotly.express as px
from dash import dcc, html, Output, Input, callback

# Composant Dash pour le scatter plot
scatter_component = html.Div([
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
```

## **Ajouter le scatter plot à `app.py`**

Modifie `app.py` pour inclure le module du scatter plot :

```python
import dash
from dash import html, dcc
from src.components.upload import upload_component
from src.components.scatter_plot import scatter_component

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Dashboard Ovizio"),
    upload_component,  # Composant d'importation
    scatter_component  # Composant scatter plot
])

if __name__ == "__main__":
    app.run_server(debug=True)
```

## **Tester l'application**

1. Lance l'application :

   ```bash
   python app.py
   ```

2. Ouvre **http://127.0.0.1:8050/** dans ton navigateur.

3. **Importe un fichier CSV**.

4. **Sélectionne deux colonnes** pour voir le scatter plot.

## **Créer le module de l'histogramme (`histogram.py`)**

Crée un fichier `components/histogram.py` et ajoute ce code :

```python
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
```

## **Ajouter l'histogramme à `app.py`**

Modifie `app.py` pour inclure le module de l'histogramme :

```python
import dash
from dash import html
from src.components.upload import upload_component
from src.components.scatter_plot import scatter_component
from src.components.histogram import histogram_component

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Dashboard Ovizio"),
    upload_component,  # Composant d'importation
    scatter_component,  # Scatter plot
    histogram_component  # Histogramme
])

if __name__ == "__main__":
    app.run_server(debug=True)
```

## **Tester l'application**

1. **Lance l'application** :

   ```bash
   python app.py
   ```

2. **Ouvre** **http://127.0.0.1:8050/**.

3. **Importe un fichier CSV**.

4. **Sélectionne une colonne** pour afficher l'histogramme.