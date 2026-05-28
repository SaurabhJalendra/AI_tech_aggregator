"""Bounded, sanitized prompt context for LLM narration."""



from __future__ import annotations



import json

from typing import Any



from src.schemas.payload_sanitizer import sanitize_nested

from src.services.explanation_fidelity import build_narration_system_addendum





def _safe_shortlist(shortlist: Any) -> str:

    if not isinstance(shortlist, list):

        return ""

    slugs = [str(s)[:64] for s in shortlist[:8] if isinstance(s, (str, int))]

    return ",".join(slugs)





def format_server_trace_for_prompt(trace: dict[str, Any] | None) -> str | None:

    """Server-only advisor trace — never accept client-provided trace blobs."""

    if not isinstance(trace, dict):

        return None

    shortlist = _safe_shortlist(trace.get("shortlist"))

    if not shortlist:

        return None

    return f"Deterministic shortlist (server): {shortlist}"





def format_prompt_context(

    validated_context: dict[str, Any],

    *,

    server_explain: dict[str, Any] | None = None,

    server_trace: dict[str, Any] | None = None,

) -> str:

    """Build prompt-safe context from validated client fields + server metadata."""

    lines: list[str] = []



    active_task = validated_context.get("active_task")

    if active_task:

        lines.append(f"Active user task: {str(active_task)[:500]}")



    option_answer = validated_context.get("option_answer")

    if isinstance(option_answer, dict):

        question_id = option_answer.get("question_id")

        answer = option_answer.get("answer_label") or option_answer.get("answer_id")

        if question_id is not None or answer is not None:

            lines.append(

                f"Latest option-card answer: slot={question_id or 'unknown'}, "

                f"value={answer if answer is not None else 'unknown'}"

            )



    resolved = validated_context.get("resolved_intent_id")

    if resolved:

        lines.append(f"Resolved intent (do not re-clarify): {resolved}")



    active_playbook = validated_context.get("active_playbook_id")

    if active_playbook:

        lines.append(f"Active playbook: {active_playbook}")



    constraint_state = validated_context.get("constraint_state")

    if isinstance(constraint_state, dict) and constraint_state.get("slots"):

        slot_summary: dict[str, Any] = {}

        for key, slot in (constraint_state.get("slots") or {}).items():

            if isinstance(slot, dict) and "value" in slot:

                slot_summary[str(key)[:64]] = slot.get("value")

        if slot_summary:

            summary_json = json.dumps(slot_summary, sort_keys=True, default=str)

            lines.append("Canonical ConstraintState slots: " + summary_json[:1500])



    if isinstance(server_explain, dict):

        addendum = build_narration_system_addendum(server_explain)

        if addendum:

            lines.append(str(sanitize_nested(addendum))[:2000])



    trace_line = format_server_trace_for_prompt(server_trace)

    if trace_line:

        lines.append(trace_line)



    current_panel = validated_context.get("current_panel")

    if current_panel:

        lines.append(f"Current right panel: {current_panel}")



    if validated_context.get("strategy_branch_id"):

        lines.append(f"Strategy branch: {validated_context['strategy_branch_id']}")



    continuity = validated_context.get("consulting_continuity")

    if continuity:

        lines.append(f"Consulting continuity: {str(continuity)[:500]}")



    if lines:

        lines.append(

            "Instruction: honor ConstraintState. Do not invent constraints or re-ask answered slots."

        )



    return "\n".join(lines)


