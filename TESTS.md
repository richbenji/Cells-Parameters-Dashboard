# Tests

## Lancer les tests

```bash
pip install -r requirements-dev.txt
pytest
```

`pytest` découvre automatiquement les fichiers `test_*.py` du dossier `tests/`
(voir `pytest.ini`) et exécute chaque fonction dont le nom commence par `test_`.
Un test réussit s'il se termine sans erreur ; chaque `assert` faux le fait échouer.

## Organisation

| Fichier | Ce qu'il vérifie |
|---|---|
| `conftest.py` | Configuration commune : base temporaire et fixtures |
| `test_data_processing.py` | Lecture et validation des CSV, libellés des features |
| `test_database.py` | Import, lecture, suppression, sécurité des requêtes SQL |
| `test_app.py` | Route `/health` et construction des figures |

## Isolation de la base

Les tests n'utilisent jamais la vraie base. `conftest.py` définit `DATA_DIR`
vers un dossier temporaire **avant** d'importer `src` (la configuration lit
cette variable à l'import). Une fixture `clean_db`, appliquée automatiquement à
chaque test, vide la base avant son exécution : les tests sont indépendants les
uns des autres et peuvent s'exécuter dans n'importe quel ordre.

## Fixtures

- `clean_db` (automatique) : base vide avant chaque test.
- `make_df` : fabrique un DataFrame synthétique avec les 26 colonnes
  attendues. Le nombre de lignes et la graine aléatoire sont réglables ; une
  même graine redonne les mêmes valeurs, ce qui rend les tests reproductibles.

## Ce que couvrent les tests

**Lecture des CSV**
- séparateur virgule ou point-virgule détecté automatiquement ;
- erreur explicite qui nomme les colonnes manquantes ;
- refus d'un fichier sans cellule ;
- valeurs illisibles converties en `NaN` plutôt que de bloquer l'import.

**Base de données**
- import et comptage des cellules ;
- refus des noms de dataset en double, sans rien enregistrer à moitié ;
- lecture de plusieurs datasets avec le nom de chacun ;
- **sécurité :** un nom de colonne qui ressemble à une injection SQL est refusé ;
- suppression en cascade : les cellules d'un dataset supprimé disparaissent, celles
  des autres restent.

**Application**
- `/health` répond 200 avec la base disponible ;
- les graphiques ne plantent pas sans donnée ;
- une série et une couleur par dataset ;
- le cas où X et Y sont la même feature.

## Ce qui n'est pas testé

- Les callbacks Dash (import et suppression via l'interface) : ils demandent un
  navigateur piloté, par exemple avec `dash[testing]` et Selenium.
- Le rendu visuel des graphiques : on vérifie leur structure, pas leur apparence.
- Le conteneur : le `HEALTHCHECK` se vérifie à la main avec `podman ps`.
