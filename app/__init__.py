from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
import os

db = SQLAlchemy()
csrf = CSRFProtect()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = 'secret-key-123'  # Ganti dengan key lebih kuat di production
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://faceuser:mypassword@localhost/facerecog_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Init extensions
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    # Import User model for login manager
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    login_manager.login_view = 'main.login'  # Redirect ke route login kalau belum login

    # Import and register routes
    from .routes import main
    app.register_blueprint(main)

    return app
