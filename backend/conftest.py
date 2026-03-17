"""Shared test fixtures."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_db():
    """Create a mock async database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def sample_module():
    """Create a sample module object for testing."""
    module = MagicMock()
    module.id = uuid.uuid4()
    module.slug = "pinecone"
    module.name = "Pinecone"
    module.tagline = "Managed vector database"
    module.description = "A managed vector database for AI"
    module.status = "stable"
    module.version = "1.0.0"
    module.pricing_model = "freemium"
    module.technical_specs = {"max_dimensions": 20000}
    module.primary_use_cases = ["Semantic search", "RAG"]
    module.supported_operations = ["upsert", "query", "delete"]
    module.comparison_scores = {
        "performance": {"score": 8, "justification": "Fast queries", "normalized": 0.8},
        "scalability": {"score": 9, "justification": "Auto-scaling", "normalized": 0.9},
    }
    module.code_examples = []
    module.alternatives = [{"slug": "weaviate"}]
    module.complements = [{"slug": "openai", "role": "embeddings"}]
    module.pipeline_position = "storage"
    module.pipeline_predecessors = ["embeddings"]
    module.pipeline_successors = ["retrieval"]
    module.category = MagicMock()
    module.category.slug = "vector_databases"
    module.category.name = "Vector Storage & Indexing"
    module.knowledge_entries = []
    module.integrations = []
    module.benchmarks = []
    return module


@pytest.fixture
def sample_user():
    """Create a sample user object for testing."""
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "test@example.com"
    user.name = "Test User"
    user.tier = "pro"
    user.image_url = None
    return user
