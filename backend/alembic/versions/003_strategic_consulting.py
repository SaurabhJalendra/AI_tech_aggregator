"""Strategic consulting profile and architecture evolution persistence.

Revision ID: 003_strategic_consulting
Revises: 002_bge_dims
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "003_strategic_consulting"
down_revision = "002_bge_dims"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "consulting_profile",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
    )
    op.create_table(
        "architecture_evolution_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("selections", postgresql.JSONB(astext_type=sa.Text()), server_default="{}"),
        sa.Column("nodes_snapshot", postgresql.JSONB(astext_type=sa.Text()), server_default="[]"),
        sa.Column("constraint_snapshot", postgresql.JSONB(astext_type=sa.Text()), server_default="{}"),
        sa.Column("transition_reason", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_architecture_evolution_user_created",
        "architecture_evolution_snapshots",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_architecture_evolution_user_created", "architecture_evolution_snapshots")
    op.drop_table("architecture_evolution_snapshots")
    op.drop_column("users", "consulting_profile")
