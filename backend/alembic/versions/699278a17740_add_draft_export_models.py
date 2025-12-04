"""add_draft_export_models

Revision ID: 699278a17740
Revises: 6d1f9eb6cc85
Create Date: 2025-12-03 14:39:12.985398

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '699278a17740'
down_revision: Union[str, Sequence[str], None] = '6d1f9eb6cc85'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add draft document export tables."""
    # Document templates table
    op.create_table('document_templates',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('document_type', sa.Enum('COMPLAINT', 'MOTION', 'BRIEF', 'RESPONSE', name='documenttype'), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('html_template', sa.Text(), nullable=False),
        sa.Column('css_styles', sa.Text(), nullable=False),
        sa.Column('docx_template_key', sa.String(length=500), nullable=True),
        sa.Column('margins', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Draft documents table
    op.create_table('draft_documents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('case_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('document_type', sa.Enum('COMPLAINT', 'MOTION', 'BRIEF', 'RESPONSE', name='documenttype', create_type=False), nullable=False),
        sa.Column('content', sa.JSON(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('DRAFT', 'REVIEWED', 'EXPORTED', name='draftstatus'), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_draft_documents_case_id'), 'draft_documents', ['case_id'], unique=False)
    op.create_index(op.f('ix_draft_documents_status'), 'draft_documents', ['status'], unique=False)

    # Export jobs table
    op.create_table('export_jobs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('draft_id', sa.String(), nullable=False),
        sa.Column('case_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('format', sa.Enum('DOCX', 'PDF', name='exportformat'), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='exportjobstatus'), nullable=False),
        sa.Column('file_key', sa.String(length=500), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('page_count', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['draft_id'], ['draft_documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_export_jobs_case_id'), 'export_jobs', ['case_id'], unique=False)
    op.create_index(op.f('ix_export_jobs_draft_id'), 'export_jobs', ['draft_id'], unique=False)
    op.create_index(op.f('ix_export_jobs_status'), 'export_jobs', ['status'], unique=False)
    op.create_index(op.f('ix_export_jobs_user_id'), 'export_jobs', ['user_id'], unique=False)


def downgrade() -> None:
    """Remove draft document export tables."""
    op.drop_index(op.f('ix_export_jobs_user_id'), table_name='export_jobs')
    op.drop_index(op.f('ix_export_jobs_status'), table_name='export_jobs')
    op.drop_index(op.f('ix_export_jobs_draft_id'), table_name='export_jobs')
    op.drop_index(op.f('ix_export_jobs_case_id'), table_name='export_jobs')
    op.drop_table('export_jobs')

    op.drop_index(op.f('ix_draft_documents_status'), table_name='draft_documents')
    op.drop_index(op.f('ix_draft_documents_case_id'), table_name='draft_documents')
    op.drop_table('draft_documents')

    op.drop_table('document_templates')

    # Drop enums (PostgreSQL specific - SQLite ignores these)
    op.execute("DROP TYPE IF EXISTS exportjobstatus")
    op.execute("DROP TYPE IF EXISTS exportformat")
    op.execute("DROP TYPE IF EXISTS draftstatus")
    op.execute("DROP TYPE IF EXISTS documenttype")
