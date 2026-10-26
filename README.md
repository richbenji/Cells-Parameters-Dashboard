# Ovizio's qMod holographic camera cell parameters dashboard 

Application Dash pour visualiser les paramètres de cellules (diamètre,
circularité, hauteur optique…) issus de captures Ovizio qMod.

![dashboard1](/run/media/richard/PROGRAMMATION/Projets/Cell-Parameters-Dashboard/dashboard1.png)

![dashboard2](/run/media/richard/PROGRAMMATION/Projets/Cell-Parameters-Dashboard/dashboard2.png)

## Fonctionnalités

- Import de datasets depuis des fichiers CSV (un ou plusieurs à la fois),
  persistés dans une base SQLite.
- Suppression de datasets.
- Scatter plot de deux paramètres au choix, une couleur par dataset.
- Histogramme d'un paramètre au choix, une couleur par dataset.
- Route de health check : `GET /health`.

## Lancer en local

Python 3.12+ recommandé.

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m src.main
```

L'application est disponible sur http://127.0.0.1:8050.
La base est créée dans `data/ovizio.db` (modifiable avec la variable
d'environnement `OVIZIO_DATA_DIR`).

## Lancer avec un conteneur

Avec Docker :

```bash
docker compose up --build
```

Avec Podman :

```bash
podman build --format docker -t cell-parameters .
podman run --rm -p 8050:8050 -v cell-parameters-data:/data cell-parameters
```

Dans le conteneur, la base est stockée dans le volume `/data` : elle survit
aux redémarrages. `--format docker` est nécessaire avec Podman pour que
l'instruction `HEALTHCHECK` soit prise en compte.

## Health check

Faire tourner l’application tourne d’abord. `curl` est un simple client : il envoie une requête à une adresse, et c’est le serveur qui répond. Si rien n’écoute sur le port 8050, tu obtiens `Connection refused`.

```bash
curl -i http://127.0.0.1:8050/health
# 200 {"database":"up","status":"ok"}   |   503 si la base est inaccessible
```

Pas besoin de curl avec Podman. Le `HEALTHCHECK` du Dockerfile fait déjà cet appel tout seul toutes les 30 secondes. Pour voir le résultat :

```bash
podman ps
```

La colonne STATUS affiche `(healthy)` après quelques secondes, ou `(unhealthy)` si `/health` échoue. Pour un test sans lancer l’application à la main, `pytest` le couvre aussi : le test `test_health_endpoint` appelle la route directement, sans serveur.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Les tests utilisent une base SQLite temporaire, jamais celle de l'application.

## Structure

```
src/
├── config.py           # chemins, liste des colonnes, valeurs par défaut
├── database.py         # SQL : tables datasets et cells, import, lecture, suppression
├── data_processing.py  # lecture et validation des CSV, libellés des features
├── plots.py            # figures Plotly (scatter, histogramme)
├── layout.py           # composants Dash (onglets, tableau, menus)
├── callbacks.py        # interactions : import, suppression, graphiques
└── main.py             # point d'entrée, route /health
tests/                  # tests pytest
Dockerfile  docker-compose.yml  requirements.txt
```

## Modèle de données

- `datasets(id, name UNIQUE, cell_count, imported_at)`
- `cells(dataset_id → datasets.id ON DELETE CASCADE, <26 colonnes numériques>)`

Le nom d'un dataset est le nom du fichier CSV sans son extension. Un CSV doit
contenir les 26 colonnes produites par qMod (voir `src/config.py`).
