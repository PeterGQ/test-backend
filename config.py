import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

class Config:
    """
    Base configuration class. Contains default configuration settings
    and settings applicable to all environments.
    """
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-very-hard-to-guess-secret-key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://myuser:mypassword@localhost:5432/mytemplate_db'
