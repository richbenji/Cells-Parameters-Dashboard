"""Test rapide de l'étape 1 : python test_step1.py Donor-A-activated.csv"""
import sys
from pathlib import Path

from src import database as db
from src.data_processing import load_csv

path = Path(sys.argv[1])
db.init_db()

name, df = load_csv(path.name, path.read_bytes())
print(f"Lu : {name}, {len(df)} cellules")

if db.dataset_exists(name):
    print("Déjà importé, on passe l'import.")
else:
    print("Importé avec l'id", db.import_dataset(name, df))

print(db.list_datasets())
cells = db.get_cells([1], ["EquivalentCellDiameterFeature", "CircularityFeature"])
print(cells.head())
