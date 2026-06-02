"""Sanitizer must preserve cited benchmark prose; flag only uncited claims."""

from src.services.response_sanitizer import SanitizationReport, sanitize_advisor_text

CITED_SENTENCES = [
    "Pinecone documents 99.9% uptime in their SLA for production tiers.",
    "Cohere rerankers report 10–20% recall improvement on BEIR in their benchmark blog.",
    "According to Weaviate's docs, hybrid search can improve recall by ~15% on mixed corpora.",
    "Measured on our eval set, pgvector HNSW recall was within 2% of dedicated vector DBs.",
    "The vendor study cites 40% lower p95 latency after enabling the dedicated index tier.",
]


def test_sanitizer_preserves_cited_metrics():
    report = SanitizationReport()
    joined = "\n".join(CITED_SENTENCES)
    cleaned = sanitize_advisor_text(joined, report=report)

    assert cleaned == joined.strip()
    flagged = [a for a in report.actions if a.rule == "uncited_metric_claim_flagged"]
    assert flagged == []


def test_sanitizer_flags_uncited_metric_without_citation_cue():
    report = SanitizationReport()
    text = "Teams often see 25% faster answers after switching models with no proof."
    cleaned = sanitize_advisor_text(text, report=report)

    assert "25%" in cleaned
    assert any(a.rule == "uncited_metric_claim_flagged" for a in report.actions)
