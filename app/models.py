from app import db
from datetime import datetime
from flask_login import UserMixin

# =========================
# USUARIO
# =========================
class User(UserMixin, db.Model):
    __tablename__ = 'users'  # 👈 evita palabra reservada "user" en Postgres
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, index=True, nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(150), nullable=False)
    rol = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f'<User {self.id} {self.email}>'


# =========================
# PRODUCTO
# =========================
class Producto(db.Model):
    __tablename__ = 'producto'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(255), nullable=False)
    caracteristicas = db.Column(db.String(255), nullable=True)
    precio = db.Column(db.Integer, nullable=False)  # si prefieres decimales finos, cambia a Float
    stock = db.Column(db.Integer, nullable=False)
    talla = db.Column(db.String(10), nullable=False)
    tipo_producto = db.Column(db.String(50), nullable=False)   # Polerón, Chaqueta, etc.
    marca = db.Column(db.String(100), nullable=False)
    genero = db.Column(db.String(20), nullable=False)          # Hombre/Mujer

    # Compatibilidad con archivos en /static/uploads
    imagen_local = db.Column(db.String(255), nullable=True)    # nombre de archivo (opcional)

    # Almacenamiento embebido (Base64) - opcional
    imagen_b64 = db.Column(db.Text, nullable=True)             # solo el contenido base64 (sin prefijo data:)
    imagen_mime = db.Column(db.String(50), nullable=True)      # ej: 'image/png' o 'image/jpeg'
    qr_b64 = db.Column(db.Text, nullable=True)                 # QR del código de barras en base64
    qr_mime = db.Column(db.String(50), nullable=True, default='image/png')

    codigo_barras = db.Column(db.String(20), unique=True, index=True, nullable=True)

    ventas = db.relationship('Venta', backref='producto', cascade="all, delete-orphan")

    # Helpers para usar en templates: <img src="{{ producto.imagen_data_url }}">
    @property
    def imagen_data_url(self):
        if self.imagen_b64 and self.imagen_mime:
            return f"data:{self.imagen_mime};base64,{self.imagen_b64}"
        if self.imagen_local:  # fallback: archivo en /static/uploads
            from flask import url_for
            try:
                return url_for('static', filename=f'uploads/{self.imagen_local}')
            except Exception:
                return None
        return None

    @property
    def qr_data_url(self):
        if self.qr_b64 and (self.qr_mime or 'image/png'):
            mime = self.qr_mime or 'image/png'
            return f"data:{mime};base64,{self.qr_b64}"
        return None

    def __repr__(self):
        return f'<Producto {self.id} {self.nombre}>'


# =========================
# VENTA
# =========================
class Venta(db.Model):
    __tablename__ = 'venta'

    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    usuario_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 👈 apuntar a 'users.id'
    cantidad = db.Column(db.Integer, nullable=False)
    metodo_pago = db.Column(db.String(50), nullable=False)
    cliente = db.Column(db.String(120), nullable=True)  # solo si es venta fiada
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship('User', backref='ventas')

    def __repr__(self):
        return f'<Venta {self.id} - Prod {self.producto_id} - User {self.usuario_id}>'
