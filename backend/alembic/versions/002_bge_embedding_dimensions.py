"""BGE-large-en-v1.5 embedding dimensions (1024).

Revision ID: 002_bge_dims
Revises: 001_initial
Create Date: 2026-05-19
"""

from alembic import op

revision = "002_bge_dims"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Existing OpenAI 1536-d vectors are incompatible with BGE; drop and recreate.
    op.execute("ALTER TABLE module_knowledge DROP COLUMN IF EXISTS embedding")
    op.execute("ALTER TABLE module_knowledge ADD COLUMN embedding vector(1024)")


def downgrade() -> None:
    op.execute("ALTER TABLE module_knowledge DROP COLUMN IF EXISTS embedding")
    op.execute("ALTER TABLE module_knowledge ADD COLUMN embedding vector(1536)")
