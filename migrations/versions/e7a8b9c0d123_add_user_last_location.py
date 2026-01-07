"""add user last location

Revision ID: e7a8b9c0d123
Revises: d4e5f6a7b890
Create Date: 2026-01-04 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e7a8b9c0d123'
down_revision = 'd4e5f6a7b890'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('user', sa.Column('last_latitude', sa.Float(), nullable=True))
    op.add_column('user', sa.Column('last_longitude', sa.Float(), nullable=True))
    op.add_column('user', sa.Column('last_seen', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('user', 'last_seen')
    op.drop_column('user', 'last_longitude')
    op.drop_column('user', 'last_latitude')
