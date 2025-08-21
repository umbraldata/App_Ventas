from app import app, db
from app.models import *

with app.app_context():
    db.create_all()
    print("DB creada/actualizada ✅")

