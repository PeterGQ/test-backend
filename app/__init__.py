from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .extensions import db, migrate
from flask_cors import CORS
from config import Config
import os
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

# 1. Initialize Sentry before your app runs
sentry_sdk.init(
    # 2. Get the DSN from an environment variable
    dsn=os.environ.get("SENTRY_DSN"),
    
    # 3. Add the FlaskIntegration to automatically capture errors
    integrations=[
        FlaskIntegration(),
    ],

    # 4. Set the environment (e.g., 'production', 'staging')
    environment=os.environ.get("SENTRY_ENVIRONMENT"),
    enable_logs=True,

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    traces_sample_rate=1.0
)

def create_app(config_class=Config):
    """
    The application factory function.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with the app instance
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app) # Enable Cross-Origin Resource Sharing

    # Import models here to ensure they are registered with SQLAlchemy
    # This is a common pattern to avoid circular imports
    from app import models

    # Register Blueprints for routes here if you have them
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
