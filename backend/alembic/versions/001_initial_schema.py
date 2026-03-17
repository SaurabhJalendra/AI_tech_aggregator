"""Initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-02-24 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Teams
    op.create_table(
        "teams",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("max_members", sa.Integer, default=10),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("name", sa.String(255)),
        sa.Column("image_url", sa.String(500)),
        sa.Column("tier", sa.String(20), server_default="free"),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("teams.id")),
        sa.Column("api_key", sa.String(64), unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Module Categories
    op.create_table(
        "module_categories",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("slug", sa.String(50), unique=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("display_order", sa.Integer, default=0),
        sa.Column("icon", sa.String(50)),
    )

    # Modules
    op.create_table(
        "modules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category_id", sa.Integer, sa.ForeignKey("module_categories.id"), nullable=False),
        sa.Column("subcategory", sa.String(100)),
        sa.Column("status", sa.String(20), server_default="stable"),
        sa.Column("version", sa.String(20), server_default="1.0.0"),
        sa.Column("tagline", sa.String(500)),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("logo_url", sa.String(500)),
        sa.Column("website", sa.String(500)),
        sa.Column("documentation", sa.String(500)),
        sa.Column("github_url", sa.String(500)),
        sa.Column("license", sa.String(100)),
        sa.Column("pricing_model", sa.String(50)),
        sa.Column("technical_specs", postgresql.JSON, server_default="{}"),
        sa.Column("primary_use_cases", postgresql.JSON, server_default="[]"),
        sa.Column("supported_operations", postgresql.JSON, server_default="[]"),
        sa.Column("comparison_scores", postgresql.JSON, server_default="{}"),
        sa.Column("code_examples", postgresql.JSON, server_default="[]"),
        sa.Column("alternatives", postgresql.JSON, server_default="[]"),
        sa.Column("complements", postgresql.JSON, server_default="[]"),
        sa.Column("pipeline_position", sa.String(50)),
        sa.Column("pipeline_predecessors", postgresql.JSON, server_default="[]"),
        sa.Column("pipeline_successors", postgresql.JSON, server_default="[]"),
        sa.Column("spec_hash", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Module Knowledge (with pgvector embedding)
    op.create_table(
        "module_knowledge",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "module_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("modules.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("topic", sa.String(500), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("tags", postgresql.ARRAY(sa.String(50)), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.execute("ALTER TABLE module_knowledge ADD COLUMN embedding vector(1536)")

    # Module Integrations
    op.create_table(
        "module_integrations",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "module_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("modules.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("target_slug", sa.String(100), nullable=False),
        sa.Column("integration_type", sa.String(20), nullable=False),
    )

    # Benchmarks
    op.create_table(
        "benchmarks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "module_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("modules.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("value", sa.Numeric(20, 6), nullable=False),
        sa.Column("unit", sa.String(50), nullable=False),
        sa.Column("context", sa.Text),
        sa.Column("run_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("runner_version", sa.String(20)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Conversations
    op.create_table(
        "conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(500)),
        sa.Column("summary", sa.Text),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("total_tokens", sa.Integer, server_default="0"),
        sa.Column("total_cost_usd", sa.Numeric(10, 6), server_default="0"),
        sa.Column("message_count", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Messages
    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", postgresql.JSON, nullable=False),
        sa.Column("panel_commands", postgresql.JSON),
        sa.Column("token_count", sa.Integer),
        sa.Column("cost_usd", sa.Numeric(10, 6)),
        sa.Column("sequence_num", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Comparisons (cached)
    op.create_table(
        "comparisons",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("module_slugs", postgresql.ARRAY(sa.String(100)), nullable=False),
        sa.Column("dimensions", postgresql.ARRAY(sa.String(100)), nullable=False),
        sa.Column("weights", postgresql.JSON),
        sa.Column("result", postgresql.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Usage Records
    op.create_table(
        "usage_records",
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
            sa.ForeignKey("conversations.id"),
        ),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("tokens_used", sa.Integer, server_default="0"),
        sa.Column("cost_usd", sa.Numeric(10, 6), server_default="0"),
        sa.Column("metadata", postgresql.JSON),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Usage Aggregates
    op.create_table(
        "usage_aggregates",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("period_type", sa.String(10), nullable=False),
        sa.Column("period_start", sa.Date, nullable=False),
        sa.Column("total_tokens", sa.BigInteger, server_default="0"),
        sa.Column("total_cost_usd", sa.Numeric(10, 4), server_default="0"),
        sa.Column("total_requests", sa.Integer, server_default="0"),
    )

    # Research Updates
    op.create_table(
        "research_updates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("module_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("modules.id")),
        sa.Column("source", sa.String(200), nullable=False),
        sa.Column("finding_type", sa.String(50), nullable=False),
        sa.Column("summary", sa.Text, nullable=False),
        sa.Column("raw_data", postgresql.JSON),
        sa.Column("applied", sa.Boolean, server_default="false"),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Expansion Candidates
    op.create_table(
        "expansion_candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category_slug", sa.String(50)),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("evidence", postgresql.JSON, nullable=False),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("spec_draft", postgresql.JSON),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Indexes
    op.create_index("ix_modules_slug", "modules", ["slug"], unique=True)
    op.create_index("ix_modules_category_id", "modules", ["category_id"])
    op.create_index("ix_module_knowledge_module_id", "module_knowledge", ["module_id"])
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"])
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    op.create_index("ix_usage_records_user_id", "usage_records", ["user_id"])


def downgrade() -> None:
    op.drop_table("expansion_candidates")
    op.drop_table("research_updates")
    op.drop_table("usage_aggregates")
    op.drop_table("usage_records")
    op.drop_table("comparisons")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("benchmarks")
    op.drop_table("module_integrations")
    op.drop_table("module_knowledge")
    op.drop_table("modules")
    op.drop_table("module_categories")
    op.drop_table("users")
    op.drop_table("teams")
