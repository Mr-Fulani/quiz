"""Create tasks table

Revision ID: 985d1ace9850
Revises: f4ba216f94ed
Create Date: 2024-09-20 20:39:21.933557

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '985d1ace9850'
down_revision: Union[str, None] = 'f4ba216f94ed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
