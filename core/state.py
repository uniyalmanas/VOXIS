from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Intent:
    name: str
    params: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    raw_text: str = ""
    source: str = "rule"
    response_text: str = ""


@dataclass
class Action:
    name: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class AppContext:
    active_app: Optional[str] = None
    last_command: str = ""
    last_intent: str = ""
    last_action: str = ""
    last_result: str = ""
    current_workflow: Optional[str] = None


@dataclass
class RuntimeState:
    primary_language: str
    fallback_language: str
    wake_words: list[str]
    is_listening: bool = True
    gesture_enabled: bool = True
    conversation_active: bool = False
    conversation_timeout_seconds: float = 18.0
    last_interaction_ts: float = 0.0
    context: AppContext = field(default_factory=AppContext)
