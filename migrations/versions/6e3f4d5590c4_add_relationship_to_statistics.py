"""Add relationship to statistics

Revision ID: 6e3f4d5590c4
Revises: 8b785d90f260
Create Date: 2024-09-26 21:04:05.886475

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6e3f4d5590c4'
down_revision: Union[str, None] = '8b785d90f260'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
