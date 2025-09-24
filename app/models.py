# Assuming you have an extensions.py file as recommended
from .extensions import db 
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

# Association table for the many-to-many relationship between Users and Roles
user_roles = db.Table('user_roles',
    db.Column('user_id', UUID(as_uuid=True), db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True)
)

# Association table for the many-to-many relationship between Roles and Permissions
role_permissions = db.Table('role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id'), primary_key=True)
)

class User(db.Model):
    __tablename__ = 'users'
    
    # This remains the primary key within your local database
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # This is the essential link to the Auth0 user profile (the 'sub' claim)
    auth0_user_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    
    # Removed password_hash, as Auth0 is the source of truth for authentication
    
    subscription_plan = db.Column(db.String(50), default='free', nullable=False)
    stripe_customer_id = db.Column(db.String(255), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Relationship to roles remains the same
    roles = db.relationship('Role', secondary=user_roles, backref=db.backref('users', lazy='dynamic'))

    def __repr__(self):
        return f'<User {self.email}>'

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))

    permissions = db.relationship('Permission', secondary=role_permissions, backref=db.backref('roles', lazy='dynamic'))

    def __repr__(self):
        return f'<Role {self.name}>'
        
    def __str__(self):
        return self.name

class Permission(db.Model):
    __tablename__ = 'permissions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False) # e.g., 'create:post', 'delete:user'
    description = db.Column(db.String(255))

    def __repr__(self):
        return f'<Permission {self.name}>'

    def __str__(self):
        return self.name

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # This foreign key correctly points to your local user ID
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=True) # Nullable for system actions
    action = db.Column(db.String(255), nullable=False)
    details = db.Column(JSONB)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    user = db.relationship('User', backref='audit_logs')

    def __repr__(self):
        return f'<AuditLog {self.action} by User {self.user_id}>'