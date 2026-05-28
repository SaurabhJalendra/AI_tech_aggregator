"""Advisor trace explain payload — user-visible filters only."""

from src.schemas.advisor_trace import AdvisorTrace, FilterRecord


def test_explain_payload_hides_comparison_layer_filters():
    trace = AdvisorTrace(
        shortlist=["gpt4", "claude"],
        filtered_out=[
            FilterRecord(slug="openai", reason="comparison_layer=foundation_model (mixed abstraction layer)"),
            FilterRecord(slug="pinecone", reason="budget=low"),
        ],
    )
    payload = trace.to_explain_payload()
    assert len(payload["applied_filters"]) == 1
    assert payload["applied_filters"][0]["slug"] == "pinecone"
    assert payload["applied_filters"][0]["reason"] == "budget=low"
