import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class ModuleCategory(Base):
    __tablename__ = "module_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    icon: Mapped[str | None] = mapped_column(String(50))

    modules: Mapped[list["Module"]] = relationship(back_populates="category")


class Module(Base):
    __tablename__ = "modules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("module_categories.id"), nullable=False
    )
    subcategory: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="stable")
    version: Mapped[str] = mapped_column(String(20), default="1.0.0")

    # Identity
    tagline: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text, nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(500))
    website: Mapped[str | None] = mapped_column(String(500))
    documentation: Mapped[str | None] = mapped_column(String(500))
    github_url: Mapped[str | None] = mapped_column(String(500))
    license: Mapped[str | None] = mapped_column(String(100))
    pricing_model: Mapped[str | None] = mapped_column(String(50))

    # Flexible JSON fields
    technical_specs: Mapped[dict] = mapped_column(JSON, default=dict)
    primary_use_cases: Mapped[list] = mapped_column(JSON, default=list)
    supported_operations: Mapped[list] = mapped_column(JSON, default=list)
    comparison_scores: Mapped[dict] = mapped_column(JSON, default=dict)
    code_examples: Mapped[list] = mapped_column(JSON, default=list)

    # Relationships data
    alternatives: Mapped[list] = mapped_column(JSON, default=list)
    complements: Mapped[list] = mapped_column(JSON, default=list)
    pipeline_position: Mapped[str | None] = mapped_column(String(50))
    pipeline_predecessors: Mapped[list] = mapped_column(JSON, default=list)
    pipeline_successors: Mapped[list] = mapped_column(JSON, default=list)

    # Spec tracking
    spec_hash: Mapped[str | None] = mapped_column(String(64))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ORM relationships
    category: Mapped[ModuleCategory] = relationship(back_populates="modules")
    knowledge_entries: Mapped[list["ModuleKnowledge"]] = relationship(
        back_populates="module", cascade="all, delete-orphan"
    )
    integrations: Mapped[list["ModuleIntegration"]] = relationship(
        back_populates="module", cascade="all, delete-orphan"
    )
    benchmarks: Mapped[list["Benchmark"]] = relationship(
        back_populates="module", cascade="all, delete-orphan"
    )


class ModuleKnowledge(Base):
    __tablename__ = "module_knowledge"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    module_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("modules.id", ondelete="CASCADE"), nullable=False
    )
    topic: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list] = mapped_column(ARRAY(String(50)), default=list)
    embedding = mapped_column(Vector(1536), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    module: Mapped[Module] = relationship(back_populates="knowledge_entries")


class ModuleIntegration(Base):
    __tablename__ = "module_integrations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    module_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("modules.id", ondelete="CASCADE"), nullable=False
    )
    target_slug: Mapped[str] = mapped_column(String(100), nullable=False)
    integration_type: Mapped[str] = mapped_column(String(20), nullable=False)

    module: Mapped[Module] = relationship(back_populates="integrations")
