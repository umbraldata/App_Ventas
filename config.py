import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'clave-secreta-segura')

    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 🔐 Claves de registro (fallbacks si no hay variables de entorno)
    ADMIN_REG_KEY = os.getenv('ADMIN_REG_KEY', 'ADMIN-123')
    VENDEDOR_REG_KEY = os.getenv('VENDEDOR_REG_KEY', 'VEND456')

    # (Opcional) ajustes de uploads legacy
    SAVE_UPLOADS_TO_DISK = os.getenv('SAVE_UPLOADS_TO_DISK', 'false').lower() == 'true'
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
