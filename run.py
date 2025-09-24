# run.py
from app import create_app, db
from app.models import User, Role, Permission, AuditLog

app = create_app()