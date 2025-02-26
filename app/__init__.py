import os
from flask import Flask
from flask_cors import CORS
from .extensions import db, mail
from .routes import auth_bp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__, static_folder='../static')

    # Configure CORS properly to allow requests from your frontend
    CORS(app, 
         resources={r"/api/*": {"origins": "https://gamatcg.com"}},
         supports_credentials=True,
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Origin"])

    # Flask Configurations
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "default-secret-key")

    # Database Configuration
    database_url = os.getenv("DATABASE_URL", "sqlite:///database.db")
    
    # Convert 'postgres://' to 'postgresql://' (required by SQLAlchemy)
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable modification tracking for performance

    # Mail Configurations
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
    app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")

    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api')
    
    return app

print("DATABASE_URL:", os.getenv("DATABASE_URL"))  # Cek apakah URL terbaca