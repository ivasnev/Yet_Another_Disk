"""Initial

Revision ID: 6058338540bc
Revises: 
Create Date: 2022-09-09 16:59:56.908475

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Enum

SystemItemType = Enum('FILE', 'FOLDER', name='type')

# revision identifiers, used by Alembic.
revision = '6058338540bc'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('items',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('url', sa.String(), nullable=True),
    sa.Column('date', sa.DateTime(timezone=True), nullable=False),
    sa.Column('parentId', sa.String(), nullable=True),
    sa.Column('type', SystemItemType, nullable=False),
    sa.Column('size', sa.BigInteger(), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk__items'))
    )
    op.create_table('relations',
    sa.Column('unit_id', sa.String(), nullable=False),
    sa.Column('relative_id', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('unit_id', 'relative_id', name=op.f('pk__relations'))
    )
    op.create_table('updates',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('date', sa.DateTime(timezone=True), nullable=False)
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('updates')
    op.drop_table('relations')
    op.drop_table('items')
    SystemItemType.drop(op.get_bind())
    # ### end Alembic commands ###