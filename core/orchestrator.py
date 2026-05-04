import time
import logging

from action_registry import ActionRegistry
from context_manager import ContextManager
from intent_parser import IntentParser
from planner import Planner
from response_engine import ResponseEngine
from state import RuntimeState


logger = logging.getLogger("VOXIS.Orchestrator")


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
        """
        Process a voice command end-to-end with error handling.
        """
        try:
            if not command or not command.strip():
                logger.warning("Empty command received")
                return "I didn't catch that. Please repeat."
            
            self.refresh_conversation()
            self.context.remember_command(command)
            
            # Parse intent
            try:
                intent = self.parser.parse(command)
                if not intent:
                    logger.warning(f"No intent parsed from: {command}")
                    return "I couldn't understand that command."
            except Exception as e:
                logger.error(f"Error parsing intent: {e}", exc_info=True)
                return "There was an error understanding your command."
            
            self.context.update_after_intent(intent)
            
            # Plan actions
            try:
                actions = self.planner.plan(intent)
                if not actions:
                    logger.debug(f"No actions planned for intent: {intent.name}")
                    return intent.response_text or "Command acknowledged."
            except Exception as e:
                logger.error(f"Error planning actions: {e}", exc_info=True)
                return "I couldn't plan how to handle that."
            
            # Execute actions
            last_text = intent.response_text
            
            for action in actions:
                try:
                    result = self.registry.execute(action)
                    
                    # Format and collect response
                    formatted_result = self.responses.format_action_result(result)
                    if formatted_result:
                        last_text = formatted_result
                    
                    # Update context
                    result_text = result.get("text", formatted_result or last_text)
                    self.context.update_after_action(action, result_text)
                    
                except Exception as e:
                    logger.error(f"Error executing action {action.name}: {e}", exc_info=True)
                    last_text = f"Error executing {action.name}"
                    self.context.update_after_action(action, last_text)
            
            return last_text or "Done."
        
        except Exception as e:
            logger.critical(f"Unexpected error in handle_command: {e}", exc_info=True)
            return "An unexpected error occurred."
