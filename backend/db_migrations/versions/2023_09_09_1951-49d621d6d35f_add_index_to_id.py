"""Add index to id

Revision ID: 49d621d6d35f
Revises: 37b2c3d37f6e
Create Date: 2023-09-09 19:51:09.375087

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '49d621d6d35f'
down_revision = '37b2c3d37f6e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('unique_values', 'adverts', type_='unique')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('unique_values', 'adverts', ['title', 'url', 'query'])
    # ### end Alembic commands ###
