import os
from dotenv import load_dotenv
import cloudinary

load_dotenv()  # En Render no es necesario, pero no molesta si queda

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'clave-secreta-segura')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # === Cloudinary ===
    CLOUDINARY_URL = os.getenv('CLOUDINARY_URL')  # NECESARIO para subir imágenes/QR

    # Carpeta local de respaldo para imágenes
    UPLOAD_FOLDER = os.path.join('app', 'static', 'uploads')

    # Claves para crear usuarios por rol
    CLAVE_ADMIN    = os.getenv('CLAVE_ADMIN')
    CLAVE_VENDEDOR = os.getenv('CLAVE_VENDEDOR')

# Inicializar Cloudinary usando la variable CLOUDINARY_URL
cloudinary.config(
    secure=True  # Fuerza HTTPS en las URLs
)
