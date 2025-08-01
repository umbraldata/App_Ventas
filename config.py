import os
from dotenv import load_dotenv

load_dotenv()  # Carga las variables del .env

class Config:
    SECRET_KEY = 'clave-secreta-segura'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
