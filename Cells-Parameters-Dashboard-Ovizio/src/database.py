import sqlite3
import pandas as pd

def init_db():
    conn = sqlite3.connect("datasets.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def insert_dataset(filename, df):
    conn = sqlite3.connect("datasets.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO datasets (filename) VALUES (?)", (filename,))
        table_name = filename.replace("-", "_").replace(".", "_")  # Nettoyage du nom
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Le fichier existe déjà
    conn.close()

def get_datasets():
    conn = sqlite3.connect("datasets.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, filename FROM datasets")
    data = cursor.fetchall()
    conn.close()
    return data

def get_dataset_data(filename):
    conn = sqlite3.connect("datasets.db")
    table_name = filename.replace("-", "_").replace(".", "_")
    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df

def delete_dataset(dataset_id, filename):
    conn = sqlite3.connect("datasets.db")
    cursor = conn.cursor()
    table_name = filename.replace("-", "_").replace(".", "_")
    cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
    cursor.execute("DELETE FROM datasets WHERE id = ?", (dataset_id,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
