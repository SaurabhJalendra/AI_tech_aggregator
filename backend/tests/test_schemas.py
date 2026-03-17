"""Tests for Pydantic schemas."""

import pytest
from pydantic import ValidationError

from src.schemas.chat import ChatRequest, PanelCommand
from src.schemas.compare import CompareRequest, Score, ComparisonResult
from src.schemas.module import ModuleSummary, ModuleDetail, CategoryResponse


class TestChatRequest:
    def test_valid_request(self):
        req = ChatRequest(message="Hello")
        assert req.message == "Hello"
        assert req.session_id is None

    def test_with_session_id(self):
        req = ChatRequest(message="Hello", session_id="abc-123")
        assert req.session_id == "abc-123"

    def test_empty_message_allowed(self):
        # Pydantic allows empty strings by default
        req = ChatRequest(message="")
        assert req.message == ""


class TestCompareRequest:
    def test_valid_request(self):
        req = CompareRequest(slugs=["pinecone", "weaviate"])
        assert len(req.slugs) == 2

    def test_too_few_slugs(self):
        with pytest.raises(ValidationError):
            CompareRequest(slugs=["single"])

    def test_too_many_slugs(self):
        with pytest.raises(ValidationError):
            CompareRequest(slugs=["a", "b", "c", "d", "e", "f"])

    def test_with_weights(self):
        req = CompareRequest(
            slugs=["a", "b"],
            weights={"performance": 2.0, "cost_efficiency": 1.5},
        )
        assert req.weights["performance"] == 2.0


class TestScore:
    def test_valid_score(self):
        s = Score(value=8.0, justification="Good performance", normalized=0.8)
        assert s.value == 8.0
        assert s.normalized == 0.8


class TestModuleSummary:
    def test_valid_summary(self):
        s = ModuleSummary(
            slug="pinecone",
            name="Pinecone",
            category="vector_databases",
            status="stable",
        )
        assert s.slug == "pinecone"
        assert s.tagline is None


class TestCategoryResponse:
    def test_valid_category(self):
        c = CategoryResponse(slug="vector_databases", name="Vector Storage")
        assert c.module_count == 0
