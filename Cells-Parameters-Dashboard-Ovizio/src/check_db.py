import sqlite3
import pandas as pd

conn = sqlite3.connect("cell_data.db")
df = pd.read_sql("SELECT * FROM cells LIMIT 5", conn)
conn.close()

print(df)