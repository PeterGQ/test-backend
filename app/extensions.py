# extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Create the SQLAlchemy instance but don't attach it to an app yet
db = SQLAlchemy()
migrate = Migrate()