from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from config import Config
import os
from flask import Flask
from flask_migrate import Migrate  # 👈 importar

app = Flask(__name__)
app.config.from_object(Config)

app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB máx

# Asegúrate que esta carpeta exista
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Extensiones
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
migrate = Migrate(app, db)  # 👈 registrar Migrate

# Importar rutas al final para evitar errores circulares
from app import routes


BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # carpeta /app

app.config['UPLOAD_FOLDER'] = os.path.join('app', 'static', 'uploads')
