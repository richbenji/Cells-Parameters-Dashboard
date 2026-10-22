# Ovizio – Cell parameters dashboard

Application Dash pour visualiser les paramètres de cellules (diamètre,
circularité, hauteur optique…) issus de captures Ovizio qMod.

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
python -m ovizio_app.main
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
podman build --format docker -t ovizio .
podman run --rm -p 8050:8050 -v ovizio-data:/data ovizio
```

Dans le conteneur, la base est stockée dans le volume `/data` : elle survit
aux redémarrages. `--format docker` est nécessaire avec Podman pour que
l'instruction `HEALTHCHECK` soit prise en compte.

## Health check

```bash
curl -i http://127.0.0.1:8050/health
# 200 {"database":"up","status":"ok"}   |   503 si la base est inaccessible
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Les tests utilisent une base SQLite temporaire, jamais celle de l'application.

## Structure

```
ovizio_app/
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
contenir les 26 colonnes produites par qMod (voir `ovizio_app/config.py`).
