"""Tests for the module spec loader."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml

from src.modules.loader import compute_spec_hash, _normalize_comparison_scores


SPECS_DIR = Path(__file__).parent.parent.parent / "modules_registry" / "specs"


def test_compute_spec_hash_deterministic():
    """Same data should produce same hash."""
    data = {"meta": {"slug": "test"}, "identity": {"description": "Test module"}}
    hash1 = compute_spec_hash(data)
    hash2 = compute_spec_hash(data)
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 hex


def test_compute_spec_hash_different_data():
    """Different data should produce different hash."""
    data1 = {"meta": {"slug": "test1"}}
    data2 = {"meta": {"slug": "test2"}}
    assert compute_spec_hash(data1) != compute_spec_hash(data2)


def test_normalize_comparison_scores():
    """Test score normalization."""
    dims = {
        "performance": {"score": 8, "justification": "Fast"},
        "scalability": {"score": 6, "justification": "Good"},
    }
    result = _normalize_comparison_scores(dims)

    assert result["performance"]["score"] == 8
    assert result["performance"]["normalized"] == 0.8
    assert result["scalability"]["score"] == 6
    assert result["scalability"]["normalized"] == 0.6


def test_normalize_comparison_scores_empty():
    """Empty dims should return empty dict."""
    assert _normalize_comparison_scores({}) == {}


def test_all_spec_files_are_valid_yaml():
    """All YAML spec files should parse without errors."""
    if not SPECS_DIR.exists():
        pytest.skip("Specs directory not found")

    for spec_file in SPECS_DIR.glob("*.yaml"):
        with open(spec_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        assert data is not None, f"{spec_file.name} is empty"
        assert "meta" in data, f"{spec_file.name} missing 'meta'"
        assert "slug" in data["meta"], f"{spec_file.name} missing 'meta.slug'"
        assert "name" in data["meta"], f"{spec_file.name} missing 'meta.name'"
        assert "category" in data["meta"], f"{spec_file.name} missing 'meta.category'"


def test_spec_slugs_are_unique():
    """All spec files should have unique slugs."""
    if not SPECS_DIR.exists():
        pytest.skip("Specs directory not found")

    slugs = []
    for spec_file in SPECS_DIR.glob("*.yaml"):
        with open(spec_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        slugs.append(data["meta"]["slug"])

    assert len(slugs) == len(set(slugs)), f"Duplicate slugs found: {[s for s in slugs if slugs.count(s) > 1]}"


def test_spec_categories_are_valid():
    """All spec categories should be from the allowed list."""
    valid_categories = {
        "data_ingestion", "chunking", "embeddings", "vector_databases",
        "retrieval", "rag_architectures", "llm_layer", "agent_systems",
        "evaluation", "caching", "fine_tuning", "deployment",
        "voice_conversational", "workflow_orchestration", "security_compliance",
        "search_discovery", "specialized_applications", "infrastructure_comparison",
    }

    if not SPECS_DIR.exists():
        pytest.skip("Specs directory not found")

    for spec_file in SPECS_DIR.glob("*.yaml"):
        with open(spec_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        category = data["meta"]["category"]
        assert category in valid_categories, f"{spec_file.name} has invalid category: {category}"
