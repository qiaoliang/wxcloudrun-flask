"""add_profile_view_logs_table

Revision ID: 20250108_add_profile_view_logs_table
Revises: 20250108_add_user_medical_history_table
Create Date: 2025-01-08

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '20250108_add_profile_view_logs_table'
down_revision = '20250108_add_user_medical_history_table'
branch_labels = None
depends_on = None


def upgrade():
    # Create profile_view_logs table
    op.create_table(
        'profile_view_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('viewer_id', sa.Integer(), nullable=False),
        sa.Column('viewed_user_id', sa.Integer(), nullable=False),
        sa.Column('ward_user_id', sa.Integer(), nullable=True),
        sa.Column('community_id', sa.Integer(), nullable=False),
        sa.Column('view_type', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.now),
        sa.ForeignKeyConstraint(['viewer_id'], ['users.user_id']),
        sa.ForeignKeyConstraint(['viewed_user_id'], ['users.user_id']),
        sa.ForeignKeyConstraint(['ward_user_id'], ['users.user_id']),
        sa.ForeignKeyConstraint(['community_id'], ['communities.community_id'])
    )

    # Create indexes for better query performance
    op.create_index('idx_profile_view_logs_viewer_id', 'profile_view_logs', ['viewer_id'])
    op.create_index('idx_profile_view_logs_viewed_user_id', 'profile_view_logs', ['viewed_user_id'])
    op.create_index('idx_profile_view_logs_community_id', 'profile_view_logs', ['community_id'])
    op.create_index('idx_profile_view_logs_created_at', 'profile_view_logs', ['created_at'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_profile_view_logs_created_at', 'profile_view_logs')
    op.drop_index('idx_profile_view_logs_community_id', 'profile_view_logs')
    op.drop_index('idx_profile_view_logs_viewed_user_id', 'profile_view_logs')
    op.drop_index('idx_profile_view_logs_viewer_id', 'profile_view_logs')

    # Drop table
    op.drop_table('profile_view_logs')
