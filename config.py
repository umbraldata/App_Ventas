import os
from dotenv import load_dotenv

# Cargar variables del archivo .env en local
load_dotenv()

class Config:
    # === Configuración base ===
    SECRET_KEY = os.getenv('SECRET_KEY', 'clave-secreta-segura')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # === Cloudinary ===
    # URL de conexión completa (no poner aquí la API Key ni Secret sueltos)
    CLOUDINARY_URL = os.getenv('CLOUDINARY_URL')  # Formato: cloudinary://<api_key>:<api_secret>@<cloud_name>

    # Carpeta local para respaldo de imágenes (opcional)
    UPLOAD_FOLDER = os.path.join('app', 'static', 'uploads')

    # Claves para crear usuarios por rol
    CLAVE_ADMIN = os.getenv('CLAVE_ADMIN')
    CLAVE_VENDEDOR = os.getenv('CLAVE_VENDEDOR')

