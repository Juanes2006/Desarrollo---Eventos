"""Corrección de eliminación de tabla

Revision ID: a473e62d034d
Revises: f117105b9a1e
Create Date: 2025-03-17 21:58:41.133197

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'a473e62d034d'
down_revision = 'f117105b9a1e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('eventos', schema=None) as batch_op:
        batch_op.alter_column('cobro',
               existing_type=mysql.FLOAT(),
               type_=sa.String(length=2),
               nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('eventos', schema=None) as batch_op:
        batch_op.alter_column('cobro',
               existing_type=sa.String(length=2),
               type_=mysql.FLOAT(),
               nullable=True)

    # ### end Alembic commands ###
