import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_session import Session
from flask_talisman import Talisman
from flask_mail import Mail

# Load environment variables from .env
if os.path.exists('.env'):
    from dotenv import load_dotenv
    load_dotenv()

# Create Flask app
app = Flask(__name__)
# SQLite Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Initialize extensions
db = SQLAlchemy()
mail = Mail()

def create_app():
    
    db.init_app(app)
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
    
    # Mail Configuration
    app.config.update(
        MAIL_SERVER=os.environ.get('MAIL_SERVER', 'smtp.gmail.com'),
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USERNAME=os.environ.get('MAIL_USERNAME'),
        MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD'),
        MAIL_DEFAULT_SENDER=os.environ.get('MAIL_DEFAULT_SENDER'),
        ADMINS=[os.environ.get('MAIL_ADMIN_DEFAULT_SENDER')]
    )
    
    # Initialize extensions with app
    mail.init_app(app)

    with app.app_context():
        try:
            # Register blueprints
            from .views.routes import routes_bp
            from .api.chat import chat_bp
            
            app.register_blueprint(routes_bp)
            app.register_blueprint(chat_bp, url_prefix="/app")
            # Initialize database
            from .database.models import User, Conversations, Files, Contact_Forms
            db.create_all(app=app)
            print("Database created successfully")

        except Exception as e:
            print(f"Error creating database: {e}")
    
    return app