from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str


class PanelCommand(BaseModel):
    action: str  # render | update | clear
    panel: str  # welcome | architecture_diagram | comparison_table | etc.
    data: dict = {}
    title: str | None = None


class ChatStreamEvent(BaseModel):
    type: str  # text | panel_command | meta | done
    content: str | None = None
    command: PanelCommand | None = None
    session_id: str | None = None
    tokens_used: int | None = None
    cost_usd: float | None = None
