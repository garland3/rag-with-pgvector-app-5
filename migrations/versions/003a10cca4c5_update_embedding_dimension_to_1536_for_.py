"""Update embedding dimension to 1536 for OpenAI

Revision ID: 003a10cca4c5
Revises: aa86e9f5eab8
Create Date: 2025-07-03 16:16:46.407754

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003a10cca4c5'
down_revision: Union[str, Sequence[str], None] = 'aa86e9f5eab8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Clear existing embeddings since dimensions are changing
    op.execute("DELETE FROM chunks")
    
    # Alter the embedding column to use new dimensions
    op.execute("ALTER TABLE chunks ALTER COLUMN embedding TYPE vector(1536)")


def downgrade() -> None:
    """Downgrade schema."""
    # Clear existing embeddings since dimensions are changing back
    op.execute("DELETE FROM chunks")
    
    # Alter the embedding column back to original dimensions
    op.execute("ALTER TABLE chunks ALTER COLUMN embedding TYPE vector(768)")
