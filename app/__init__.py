from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
import os

app = Flask(__name__)
app.config.from_object(Config)

# ===== Claves de registro (para /registro) =====
# Si existen variables de entorno, se usan; si no, se mantiene lo definido en Config
app.config['ADMIN_REG_KEY'] = os.getenv('ADMIN_REG_KEY', app.config.get('ADMIN_REG_KEY'))
app.config['VENDEDOR_REG_KEY'] = os.getenv('VENDEDOR_REG_KEY', app.config.get('VENDEDOR_REG_KEY'))

# ===== Subidas / Uploads =====
# Carpeta absoluta dentro de app/static/uploads
UPLOAD_DIR = os.path.join(app.root_path, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_DIR
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB máx
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Bandera para guardar archivos físicos (legacy). En Render ponla en false.
app.config['SAVE_UPLOADS_TO_DISK'] = os.getenv('SAVE_UPLOADS_TO_DISK', 'false').lower() == 'true'

# ===== (Opcional) Normalizar DATABASE_URL para Postgres (Render) =====
_db_url = os.getenv('DATABASE_URL')
if _db_url:
    if _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql+psycopg2://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = _db_url

# ===== Extensiones =====
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
migrate = Migrate(app, db)

# Importar rutas al final para evitar errores circulares
from app import routes
