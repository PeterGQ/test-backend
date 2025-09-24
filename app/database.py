# database.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# 1. Define the database URL
# It's best practice to get this from an environment variable.
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://myuser:mypassword@postgres-db:5432/mytemplate_db"
)

# 2. Create the SQLAlchemy engine
# The engine is the core interface to the database.
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 3. Create a SessionLocal class
# This is a factory for creating new database sessions. Each instance
# of SessionLocal will be a new session. This is the object you were
# asking about.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Create a Base class for your models
# All of your SQLAlchemy models will inherit from this class. It allows
# SQLAlchemy's ORM features to work with your models.
Base = declarative_base()