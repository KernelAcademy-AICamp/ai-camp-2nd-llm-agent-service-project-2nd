"""add case soft delete

Revision ID: b5c6d7e8f9a0
Revises: a1b2c3d4e5f6
Create Date: 2025-12-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b5c6d7e8f9a0'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add deleted_at column to cases table for soft delete support
    op.add_column('cases', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index('ix_cases_deleted_at', 'cases', ['deleted_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_cases_deleted_at', table_name='cases')
    op.drop_column('cases', 'deleted_at')
