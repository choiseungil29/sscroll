"""add content ups or downs

Revision ID: 17d2937a72b5
Revises: d24203a8933e
Create Date: 2019-04-07 23:14:21.365621

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '17d2937a72b5'
down_revision = 'd24203a8933e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('contents', sa.Column('down', sa.Integer(), nullable=True))
    op.add_column('contents', sa.Column('up', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('contents', 'up')
    op.drop_column('contents', 'down')
    # ### end Alembic commands ###