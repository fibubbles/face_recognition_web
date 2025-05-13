from app import db
from flask_login import UserMixin

# ✅ Model untuk admin user login
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(256), nullable=False)

# ✅ Model untuk log pengesanan (pelawat & penceroboh)
class DetectionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))           # Nama pelawat atau "Unknown"
    entry_time = db.Column(db.DateTime)        # Masa masuk
    exit_time = db.Column(db.DateTime)         # Masa keluar
    duration = db.Column(db.Integer)           # Dalam saat
