from app import db
from datetime import datetime
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(150), nullable=False)
    rol = db.Column(db.String(50), nullable=False)


class Producto(db.Model):
    __tablename__ = 'producto'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(255), nullable=False)
    caracteristicas = db.Column(db.String(255))
    precio = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    talla = db.Column(db.String(10), nullable=False)
    tipo_producto = db.Column(db.String(50), nullable=False)   # Polerón, Chaqueta, etc.
    marca = db.Column(db.String(100), nullable=False)
    genero = db.Column(db.String(20), nullable=False)          # Hombre/Mujer

    # === Compatibilidad con tu versión anterior (carpeta static) ===
    imagen_local = db.Column(db.String(255))                   # ruta en /static/uploads (si existe)

    # === NUEVO: almacenamiento embebido (Base64) ===
    imagen_b64 = db.Column(db.Text)                            # solo el contenido base64 (sin prefijo data:)
    imagen_mime = db.Column(db.String(50))                     # ej: 'image/png' o 'image/jpeg'
    qr_b64 = db.Column(db.Text)                                # QR del código de barras en base64
    qr_mime = db.Column(db.String(50), default='image/png')    # por defecto PNG

    codigo_barras = db.Column(db.String(20), unique=True)

    ventas = db.relationship('Venta', backref='producto', cascade="all, delete-orphan")

    # Helpers para usar directo en templates: <img src="{{ producto.imagen_data_url }}">
    @property
    def imagen_data_url(self):
        if self.imagen_b64 and self.imagen_mime:
            return f"data:{self.imagen_mime};base64,{self.imagen_b64}"
        # fallback si aún tienes archivos en /static
        if self.imagen_local:
            from flask import url_for
            try:
                return url_for('static', filename=f'uploads/{self.imagen_local}')
            except Exception:
                return None
        return None

    @property
    def qr_data_url(self):
        if self.qr_b64 and self.qr_mime:
            return f"data:{self.qr_mime};base64,{self.qr_b64}"
        return None


class Venta(db.Model):
    __tablename__ = 'venta'

    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    metodo_pago = db.Column(db.String(50), nullable=False)
    cliente = db.Column(db.String(120))  # solo usado si es venta fiada
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship('User', backref='ventas')

    def __repr__(self):
        return f'<Venta {self.id} - Producto {self.producto_id} - Usuario {self.usuario_id}>'


