"""Add custom_data column to users table

Revision ID: 004
Revises: 003
Create Date: 2024-11-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add custom_data column to users table
    op.add_column('users', sa.Column('custom_data', sa.JSON(), nullable=True))


def downgrade() -> None:
    # Remove custom_data column from users table
    op.drop_column('users', 'custom_data')
