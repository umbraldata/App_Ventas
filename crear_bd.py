from app import app, db
from app.models import User
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

with app.app_context():
    db.create_all()

    # Crear un admin inicial si no existe
    if not User.query.filter_by(email='admin@mail.com').first():
        admin = User(
            nombre="Admin",
            apellido="Principal",
            email="admin@mail.com",
            telefono="123456789",
            password=bcrypt.generate_password_hash('admin123').decode('utf-8'),
            rol="administrador"
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin creado: admin@mail.com / admin123")
    else:
        print("✅ Base de datos creada, Admin ya existía.")
