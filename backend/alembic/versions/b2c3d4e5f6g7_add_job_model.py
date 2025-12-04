"""add job model

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2025-12-04 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add jobs table for async processing tracking"""
    op.create_table(
        'jobs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('case_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('job_type', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('evidence_id', sa.String(), nullable=True),
        sa.Column('input_data', sa.String(), nullable=True),
        sa.Column('output_data', sa.String(), nullable=True),
        sa.Column('error_details', sa.String(), nullable=True),
        sa.Column('progress', sa.String(), server_default='0', nullable=True),
        sa.Column('retry_count', sa.String(), server_default='0', nullable=True),
        sa.Column('max_retries', sa.String(), server_default='3', nullable=True),
        sa.Column('lambda_request_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_jobs_case_id'), 'jobs', ['case_id'], unique=False)
    op.create_index(op.f('ix_jobs_evidence_id'), 'jobs', ['evidence_id'], unique=False)
    op.create_index(op.f('ix_jobs_user_id'), 'jobs', ['user_id'], unique=False)


def downgrade() -> None:
    """Remove jobs table"""
    op.drop_index(op.f('ix_jobs_user_id'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_evidence_id'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_case_id'), table_name='jobs')
    op.drop_table('jobs')
