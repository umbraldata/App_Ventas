# wsgi.py
from app import app as application, db
from sqlalchemy import inspect

# Alias que usa gunicorn
app = application

def _bootstrap_db_if_needed():
    with app.app_context():
        inspector = inspect(db.engine)
        required = {'users', 'producto', 'venta'}
        existing = set(inspector.get_table_names())

        missing = required - existing
        if missing:
            print("⚙️  Creando tablas faltantes:", missing)
            db.create_all()
            print("✅ Tablas creadas")

# Ejecutar bootstrap al arrancar
_bootstrap_db_if_needed()

if __name__ == "__main__":
    app.run()
