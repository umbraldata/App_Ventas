import os
from dotenv import load_dotenv

load_dotenv()  # en Render no es necesario, pero no molesta si queda

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'clave-secreta-segura')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Claves para crear usuarios por rol
    CLAVE_ADMIN    = os.getenv('CLAVE_ADMIN')
    CLAVE_VENDEDOR = os.getenv('CLAVE_VENDEDOR')
