"""Add representative_location table

Revision ID: c2d3e4f5a678
Revises: b11a4d04a389
Create Date: 2026-01-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c2d3e4f5a678'
down_revision = 'b11a4d04a389'
branch_labels = None
depends_on = None


def upgrade():
    # No-op: representative location tracking removed
    return


def downgrade():
    # No-op: representative location tracking removed
    return
