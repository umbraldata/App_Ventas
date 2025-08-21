import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'clave-secreta-segura')

    # ===============================
    # 🔗 Base de datos
    # ===============================
    raw = os.getenv("DATABASE_URL")  # Render entrega esta variable
    if raw:
        # Asegurar que SQLAlchemy entienda bien el driver
        if raw.startswith("postgres://"):
            raw = raw.replace("postgres://", "postgresql+psycopg2://", 1)
        elif raw.startswith("postgresql://"):
            raw = raw.replace("postgresql://", "postgresql+psycopg2://", 1)

        # Forzar SSL si no lo trae
        if "sslmode=" not in raw:
            sep = "&" if "?" in raw else "?"
            raw = f"{raw}{sep}sslmode=require"

        SQLALCHEMY_DATABASE_URI = raw
    else:
        # 👉 fallback a SQLite en local
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'database.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Ajustes de pool para Render (evita errores al despertar la instancia free)
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,   # recicla conexiones cada 5 min
        "pool_size": 5,
        "max_overflow": 5,
    }

    # ===============================
    # 🔐 Claves de registro
    # ===============================
    ADMIN_REG_KEY = os.getenv('ADMIN_REG_KEY', 'ADMIN-123')
    VENDEDOR_REG_KEY = os.getenv('VENDEDOR_REG_KEY', 'VEND456')

    # ===============================
    # 📂 Uploads (compatibilidad legacy)
    # ===============================
    SAVE_UPLOADS_TO_DISK = os.getenv('SAVE_UPLOADS_TO_DISK', 'false').lower() == 'true'
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
