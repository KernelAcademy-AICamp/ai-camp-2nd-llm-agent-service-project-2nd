"""add role based UI models

Revision ID: a1b2c3d4e5f6
Revises: 6d1f9eb6cc85
Create Date: 2025-12-04 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '6d1f9eb6cc85'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add tables for role-based UI feature.

    - messages: Real-time communication between users
    - calendar_events: Scheduling for lawyers
    - investigation_records: Field recording for detectives
    - invoices: Billing and payment tracking

    Also updates user_role enum to include CLIENT and DETECTIVE.
    """
    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('case_id', sa.String(), nullable=False),
        sa.Column('sender_id', sa.String(), nullable=False),
        sa.Column('recipient_id', sa.String(), nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('attachments', sa.String(), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['recipient_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_messages_case_id', 'messages', ['case_id'], unique=False)
    op.create_index('ix_messages_sender_id', 'messages', ['sender_id'], unique=False)
    op.create_index('ix_messages_recipient_id', 'messages', ['recipient_id'], unique=False)

    # Create calendar_events table
    op.create_table(
        'calendar_events',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('case_id', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('event_type', sa.Enum('COURT', 'MEETING', 'DEADLINE', 'INTERNAL', 'OTHER', name='calendareventtype'), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('reminder_minutes', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_calendar_events_user_id', 'calendar_events', ['user_id'], unique=False)
    op.create_index('ix_calendar_events_case_id', 'calendar_events', ['case_id'], unique=False)

    # Create investigation_records table
    op.create_table(
        'investigation_records',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('case_id', sa.String(), nullable=False),
        sa.Column('detective_id', sa.String(), nullable=False),
        sa.Column('record_type', sa.Enum('LOCATION', 'PHOTO', 'VIDEO', 'AUDIO', 'MEMO', 'EVIDENCE', name='investigationrecordtype'), nullable=False),
        sa.Column('content', sa.String(), nullable=True),
        sa.Column('location_lat', sa.String(), nullable=True),
        sa.Column('location_lng', sa.String(), nullable=True),
        sa.Column('location_address', sa.String(), nullable=True),
        sa.Column('attachments', sa.String(), nullable=True),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ),
        sa.ForeignKeyConstraint(['detective_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_investigation_records_case_id', 'investigation_records', ['case_id'], unique=False)
    op.create_index('ix_investigation_records_detective_id', 'investigation_records', ['detective_id'], unique=False)

    # Create invoices table
    op.create_table(
        'invoices',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('case_id', sa.String(), nullable=False),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('lawyer_id', sa.String(), nullable=False),
        sa.Column('amount', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'PAID', 'OVERDUE', 'CANCELLED', name='invoicestatus'), nullable=False),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ),
        sa.ForeignKeyConstraint(['client_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['lawyer_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_invoices_case_id', 'invoices', ['case_id'], unique=False)
    op.create_index('ix_invoices_client_id', 'invoices', ['client_id'], unique=False)
    op.create_index('ix_invoices_lawyer_id', 'invoices', ['lawyer_id'], unique=False)


def downgrade() -> None:
    """Remove role-based UI tables."""
    # Drop invoices
    op.drop_index('ix_invoices_lawyer_id', table_name='invoices')
    op.drop_index('ix_invoices_client_id', table_name='invoices')
    op.drop_index('ix_invoices_case_id', table_name='invoices')
    op.drop_table('invoices')

    # Drop investigation_records
    op.drop_index('ix_investigation_records_detective_id', table_name='investigation_records')
    op.drop_index('ix_investigation_records_case_id', table_name='investigation_records')
    op.drop_table('investigation_records')

    # Drop calendar_events
    op.drop_index('ix_calendar_events_case_id', table_name='calendar_events')
    op.drop_index('ix_calendar_events_user_id', table_name='calendar_events')
    op.drop_table('calendar_events')

    # Drop messages
    op.drop_index('ix_messages_recipient_id', table_name='messages')
    op.drop_index('ix_messages_sender_id', table_name='messages')
    op.drop_index('ix_messages_case_id', table_name='messages')
    op.drop_table('messages')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS invoicestatus")
    op.execute("DROP TYPE IF EXISTS investigationrecordtype")
    op.execute("DROP TYPE IF EXISTS calendareventtype")
