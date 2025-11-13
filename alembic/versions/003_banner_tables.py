"""Add banner tables

Revision ID: 003
Revises: 002
Create Date: 2024-11-10 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create banners table
    op.create_table(
        'banners',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('image_url', sa.String(length=500), nullable=False),
        sa.Column('target_url', sa.String(length=500), nullable=False),
        sa.Column('alt_text', sa.String(length=255), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('target_departments', sa.JSON(), nullable=True),
        sa.Column('target_users', sa.JSON(), nullable=True),
        sa.Column('views_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('clicks_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create banner_clicks table
    op.create_table(
        'banner_clicks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('banner_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('clicked_at', sa.DateTime(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('referer', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['banner_id'], ['banners.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_banner_clicks_banner_id', 'banner_clicks', ['banner_id'])
    op.create_index('ix_banner_clicks_clicked_at', 'banner_clicks', ['clicked_at'])


def downgrade() -> None:
    op.drop_index('ix_banner_clicks_clicked_at')
    op.drop_index('ix_banner_clicks_banner_id')
    op.drop_table('banner_clicks')
    op.drop_table('banners')
