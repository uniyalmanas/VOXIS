import json
import re

from ai_brain_runtime import AIBrain
from state import Intent


class ModelRouter:
    def __init__(self):
        self.brain = AIBrain()

    def infer_intent(self, command: str, context: dict | None = None, history: list | None = None) -> Intent:
        response = self.brain.think(command, context=context, history=history)
        cleaned = response.strip()

        if "```" in cleaned:
            parts = cleaned.split("```")
            if len(parts) > 1:
                cleaned = parts[1].strip()
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:].strip()

        if "{" in cleaned and '"action"' in cleaned:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                cleaned = match.group()

        try:
            data = json.loads(cleaned)
            return Intent(
                name=data.get("action", "unknown"),
                params=data.get("params", {}),
                confidence=0.5,
                raw_text=command,
                source="model",
            )
        except json.JSONDecodeError:
            return Intent(
                name="respond",
                params={"text": response},
                confidence=0.3,
                raw_text=command,
                source="model",
                response_text=response,
            )

    def set_mode(self, mode: str) -> str:
        return self.brain.set_mode(mode)
