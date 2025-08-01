import os
from dotenv import load_dotenv

load_dotenv()  # Carga las variables del .env

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'clave-secreta-segura')  # puedes sobrescribirla desde .env
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')  # URI de la base de datos (por ejemplo para Render)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CLAVE_ADMIN = os.getenv('CLAVE_ADMIN', 'clave-super-secreta-123')  # ← Se usa para registrar administradores
