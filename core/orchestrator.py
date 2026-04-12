import time

from action_registry import ActionRegistry
from context_manager import ContextManager
from intent_parser import IntentParser
from planner import Planner
from response_engine import ResponseEngine
from state import RuntimeState


class VoiceOrchestrator:
    def __init__(self, voice_engine):
        self.voice_engine = voice_engine
        self.state = RuntimeState(
            primary_language=voice_engine.primary_language,
            fallback_language=voice_engine.fallback_language,
            wake_words=voice_engine.wake_words,
        )
        self.context = ContextManager(self.state)
        self.parser = IntentParser(self.state)
        self.planner = Planner()
        self.registry = ActionRegistry(voice_engine)
        self.responses = ResponseEngine()

    def set_languages(self, primary_language: str, fallback_language: str) -> None:
        self.state.primary_language = primary_language
        self.state.fallback_language = fallback_language

    def activate_conversation(self) -> None:
        self.state.conversation_active = True
        self.state.last_interaction_ts = time.time()

    def refresh_conversation(self) -> None:
        self.state.last_interaction_ts = time.time()

    def is_conversation_active(self) -> bool:
        if not self.state.conversation_active:
            return False

        if time.time() - self.state.last_interaction_ts <= self.state.conversation_timeout_seconds:
            return True

        self.state.conversation_active = False
        return False

    def handle_command(self, command: str) -> str:
        self.refresh_conversation()
        self.context.remember_command(command)
        intent = self.parser.parse(command)
        self.context.update_after_intent(intent)

        actions = self.planner.plan(intent)
        last_text = intent.response_text

        for action in actions:
            result = self.registry.execute(action)
            last_text = self.responses.format_action_result(result) or last_text
            self.context.update_after_action(action, result.get("text", last_text))

        return last_text
