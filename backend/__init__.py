import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_session import Session
from flask_talisman import Talisman
from flask_login import LoginManager

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
# Main application function
def create_app():
    # Create Flask app
    app = Flask(__name__)
    
    # SQLite Configuration
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Basic Configuration
    app.config['SECRET_KEY'] = os.urandom(24)
    
    # Configure static and template folders
    app.static_folder = os.path.join(os.pardir, 'static')
    app.template_folder = os.path.join(os.pardir, 'templates')
    
    # Session Configuration
    app.config['SESSION_TYPE'] = 'filesystem'
    Session(app)
    
    # CORS Configuration
    CORS(app)
    
    # Talisman Security Configuration
    Talisman(
        app,
        content_security_policy=None,
        force_https=True
    )
    
    # Initialize extensions with app
    db.init_app(app)
    
    # Register blueprints
    from .views.routes import routes_bp
    from .api.chat import chat_bp
    
    app.register_blueprint(routes_bp)
    app.register_blueprint(chat_bp, url_prefix="/app")

    login_manager = LoginManager()
    login_manager.login_view = 'routes.login'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return User.query.get(int(user_id))
    # Import models AFTER db is initialized
    from .database.models import User
    
    # Create database tables
    with app.app_context():
        db.create_all()

    return app