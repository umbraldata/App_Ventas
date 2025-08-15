# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config

import os
import cloudinary  # <- para inicializar Cloudinary

app = Flask(__name__)
app.config.from_object(Config)

# ============================
# Archivos / uploads locales
# ============================
# Define una única vez la carpeta de uploads (relativa al proyecto)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # .../app
app.config['UPLOAD_FOLDER'] = os.path.join('app', 'static', 'uploads')

# Tamaño máximo (16 MB) para subidas
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Crea la carpeta si no existe
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ============================
# Extensiones Flask
# ============================
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

migrate = Migrate(app, db)

# ============================
# Cloudinary (usa CLOUDINARY_URL)
# ============================
# Ejemplo de CLOUDINARY_URL:
# cloudinary://<api_key>:<api_secret>@<cloud_name>
cld_url = app.config.get('CLOUDINARY_URL')
if cld_url:
    cloudinary.config(
        cloudinary_url=cld_url,
        secure=True,  # fuerza HTTPS en las URLs
    )
else:
    # No detiene la app, pero te avisa en logs si no está configurado
    print("[WARN] CLOUDINARY_URL no está definido. Las subidas a Cloudinary fallarán.")

# ============================
# Importa rutas al final
# ============================
from app import routes  # noqa: E402, F401
