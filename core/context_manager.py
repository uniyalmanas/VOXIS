from collections import deque

from state import Action, Intent, RuntimeState


class ContextManager:
    def __init__(self, state: RuntimeState):
        self.state = state
        self.history: deque[dict[str, str]] = deque(maxlen=10)

    def remember_command(self, command: str) -> None:
        self.state.context.last_command = command
        self.history.append({"role": "user", "content": command})

    def update_after_intent(self, intent: Intent) -> None:
        self.state.context.last_intent = intent.name

    def update_after_action(self, action: Action, result_text: str = "") -> None:
        self.state.context.last_action = action.name
        self.state.context.last_result = result_text

        app_name = action.params.get("app_name")
        if action.name == "open_app" and app_name:
            self.state.context.active_app = app_name.lower()

        self.history.append({
            "role": "assistant",
            "content": result_text or action.name,
        })

    def recent_history(self) -> list[dict[str, str]]:
        return list(self.history)

    def summarized_context(self) -> dict[str, str]:
        return {
            "active_app": self.state.context.active_app or "",
            "last_command": self.state.context.last_command,
            "last_intent": self.state.context.last_intent,
            "last_action": self.state.context.last_action,
            "last_result": self.state.context.last_result,
        }
