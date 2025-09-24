"""seed initial roles and permissions

Revision ID: 0db1eab8c78a
Revises: e7c1d26245b0
Create Date: 2025-09-18 21:49:40.604875

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker


# revision identifiers, used by Alembic.
revision = '0db1eab8c78a'
down_revision = 'e7c1d26245b0'
branch_labels = None
depends_on = None


# Define a simple version of the Role table for the migration
# This prevents issues if the model in your main app changes later.
roles_table = sa.table('roles',
    sa.column('name', sa.String),
    sa.column('description', sa.String)
)

def upgrade():
    """Seeds the roles table with default values."""
    op.bulk_insert(roles_table,
        [
            {'name': 'user', 'description': 'Standard user with basic permissions.'},
            {'name': 'admin', 'description': 'Super user with full access and permissions.'}
        ]
    )


def downgrade():
    """Removes the seeded roles."""
    # Use raw SQL for the delete operation in the downgrade.
    # This is often simpler and safer for data migrations.
    op.execute("DELETE FROM roles WHERE name IN ('user', 'admin')")
