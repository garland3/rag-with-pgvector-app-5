"""Add ingestion jobs table

Revision ID: aa86e9f5eab8
Revises: b7b0843c091a
Create Date: 2025-07-03 15:56:44.062144

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'aa86e9f5eab8'
down_revision: Union[str, Sequence[str], None] = 'b7b0843c091a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'ingestion_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('status', sa.String(20), default='pending', nullable=False),
        sa.Column('total_files', sa.Integer, default=0, nullable=False),
        sa.Column('processed_files', sa.Integer, default=0, nullable=False),
        sa.Column('failed_files', sa.Integer, default=0, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('error_message', sa.Text),
        sa.Column('job_metadata', postgresql.JSONB),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('ingestion_jobs')
