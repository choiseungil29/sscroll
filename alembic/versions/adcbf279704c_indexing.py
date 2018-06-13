"""indexing

Revision ID: adcbf279704c
Revises: 082dfb2d2dd8
Create Date: 2018-06-10 16:14:50.106239

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'adcbf279704c'
down_revision = '082dfb2d2dd8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_contents_permanent_id'), 'contents', ['permanent_id'], unique=True)
    op.drop_constraint('contents_permanent_id_key', 'contents', type_='unique')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('contents_permanent_id_key', 'contents', ['permanent_id'])
    op.drop_index(op.f('ix_contents_permanent_id'), table_name='contents')
    # ### end Alembic commands ###
