"""update user

Revision ID: 6c1969e36d78
Revises: eebd63b34f63
Create Date: 2019-04-07 21:59:13.775408

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '6c1969e36d78'
down_revision = 'eebd63b34f63'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'signup_type')
    op.drop_column('users', 'access_token')
    op.drop_column('users', 'email')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('email', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('access_token', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('signup_type', postgresql.ENUM('NAVER', name='signuptypeenum'), autoincrement=False, nullable=True))
    # ### end Alembic commands ###