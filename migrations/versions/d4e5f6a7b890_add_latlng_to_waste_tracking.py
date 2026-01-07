"""Add latitude/longitude/updated_by to waste_tracking

Revision ID: d4e5f6a7b890
Revises: c2d3e4f5a678
Create Date: 2026-01-04 00:10:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4e5f6a7b890'
down_revision = 'c2d3e4f5a678'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('waste_tracking', schema=None) as batch_op:
        batch_op.add_column(sa.Column('latitude', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('longitude', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('updated_by', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_waste_tracking_updated_by', 'user', ['updated_by'], ['id'])


def downgrade():
    with op.batch_alter_table('waste_tracking', schema=None) as batch_op:
        batch_op.drop_constraint('fk_waste_tracking_updated_by', type_='foreignkey')
        batch_op.drop_column('updated_by')
        batch_op.drop_column('longitude')
        batch_op.drop_column('latitude')
