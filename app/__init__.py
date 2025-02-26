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

    # Database Configuration - Gunakan pg8000 sebagai driver
    db_user = os.getenv("DB_USER", "neondb_owner")
    db_password = os.getenv("DB_PASSWORD", "npg_eKmXIj89vaJu")
    db_host = os.getenv("DB_HOST", "ep-proud-frost-a1gwj4jx-pooler.ap-southeast-1.aws.neon.tech")
    db_name = os.getenv("DB_NAME", "neondb")
    
    # Buat string koneksi dengan pg8000
    database_url = f"postgresql+pg8000://{db_user}:{db_password}@{db_host}/{db_name}?ssl=true"
    
    print(f"Using database: {db_host}/{db_name}")
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Mail Configurations
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME", "timgemilanglolos@gmail.com")
    app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD", "ywvpgartwsaahlyf")

    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api')
    
    return app