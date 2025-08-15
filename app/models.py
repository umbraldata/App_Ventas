# app/models.py
from app import db
from datetime import datetime
from flask_login import UserMixin

# ──────────────────────────────────────────────────────────────────────────────
# MODELO DE USUARIO
# ──────────────────────────────────────────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id       = db.Column(db.Integer, primary_key=True)
    nombre   = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    email    = db.Column(db.String(150), unique=True, nullable=False)
    telefono = db.Column(db.String(20),  nullable=False)
    password = db.Column(db.String(150), nullable=False)
    rol      = db.Column(db.String(50),  nullable=False)

    def __repr__(self):
        return f'<User {self.id} - {self.email} ({self.rol})>'


# ──────────────────────────────────────────────────────────────────────────────
# MODELO DE PRODUCTO (con soporte Cloudinary + compatibilidad local)
# ──────────────────────────────────────────────────────────────────────────────
class Producto(db.Model):
    __tablename__ = 'producto'

    id            = db.Column(db.Integer, primary_key=True)
    nombre        = db.Column(db.String(100), nullable=False)
    descripcion   = db.Column(db.String(255), nullable=False)
    caracteristicas = db.Column(db.String(255))
    precio        = db.Column(db.Integer, nullable=False)
    stock         = db.Column(db.Integer, nullable=False)
    talla         = db.Column(db.String(8),  nullable=False)
    tipo_producto = db.Column(db.String(50), nullable=False)  # Polerón, Chaqueta, etc.
    marca         = db.Column(db.String(50), nullable=False)
    genero        = db.Column(db.String(20), nullable=False)  # Hombre/Mujer

    # ── Imagen local (legacy, ya usado por tu app). Lo conservamos:
    imagen_local  = db.Column(db.String(255))  # nombre de archivo en static/uploads

    # ── NUEVO: soporte Cloudinary
    imagen_public_id = db.Column(db.String(255), nullable=True)  # public_id de Cloudinary
    qr_public_id     = db.Column(db.String(255), nullable=True)  # public_id del QR en Cloudinary

    # Código de barras que ya usas
    codigo_barras = db.Column(db.String(20), unique=True)

    # Relación con ventas
    ventas = db.relationship(
        'Venta',
        backref='producto',
        cascade="all, delete-orphan"
    )

    # ----------------- Helpers de URL -----------------
    def get_imagen_url(self):
        """
        Devuelve URL https de la imagen en Cloudinary si imagen_public_id existe.
        Si no, hace fallback a la ruta local /static/uploads/<imagen_local>.
        """
        # Primero Cloudinary
        if self.imagen_public_id:
            try:
                import cloudinary.utils
                url, _ = cloudinary.utils.cloudinary_url(self.imagen_public_id, secure=True)
                if url:
                    return url
            except Exception:
                pass

        # Fallback: archivo local
        if self.imagen_local:
            try:
                from flask import url_for
                return url_for('static', filename=f'uploads/{self.imagen_local}')
            except RuntimeError:
                # si no hay contexto de app (por ejemplo en scripts)
                return f"/static/uploads/{self.imagen_local}"
        return None

    def get_qr_url(self):
        """
        Devuelve URL https del QR en Cloudinary si qr_public_id existe.
        No tiene fallback local porque normalmente no lo estabas guardando
        como archivo físico (si lo quieres, puedes implementarlo igual que imagen_local).
        """
        if self.qr_public_id:
            try:
                import cloudinary.utils
                url, _ = cloudinary.utils.cloudinary_url(self.qr_public_id, secure=True)
                if url:
                    return url
            except Exception:
                pass
        return None

    def __repr__(self):
        return f'<Producto {self.id} - {self.nombre}>'


# ──────────────────────────────────────────────────────────────────────────────
# MODELO DE VENTA
# ──────────────────────────────────────────────────────────────────────────────
class Venta(db.Model):
    __tablename__ = 'venta'

    id         = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    usuario_id  = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    cantidad    = db.Column(db.Integer, nullable=False)
    metodo_pago = db.Column(db.String(50), nullable=False)  # Efectivo / Débito / Crédito / Transferencia / Fiado
    cliente     = db.Column(db.String(120))                 # solo usa si es venta fiada
    fecha       = db.Column(db.DateTime, default=datetime.utcnow)

    # Relación inversa hacia User (ya la tienes)
    usuario = db.relationship('User', backref='ventas')

    def __repr__(self):
        return f'Venta {{self.id}} - Producto {{self.producto_id}} - Usuario {{self.usuario_id}}'
