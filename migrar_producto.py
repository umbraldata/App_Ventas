import sqlite3

# Cambia este nombre si tu base de datos no se llama 'database.db'
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE producto ADD COLUMN genero TEXT")
    cursor.execute("ALTER TABLE producto ADD COLUMN marca TEXT")
    print("Columnas 'genero' y 'marca' agregadas con éxito.")
except sqlite3.OperationalError as e:
    print(f"Ya existen o error: {e}")

conn.commit()
conn.close()
