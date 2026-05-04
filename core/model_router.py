import json
import re
import logging

from ai_brain_runtime import AIBrain
from state import Intent


logger = logging.getLogger("VOXIS.ModelRouter")


class ModelRouter:
    def __init__(self):
        self.brain = AIBrain()

    def _extract_json(self, text: str) -> dict | None:
        """
        Extract and parse JSON from text with improved robustness.
        Handles markdown code blocks, nested objects, etc.
        """
        text = text.strip()
        
        # Handle markdown code blocks
        if "```" in text:
            parts = text.split("```")
            if len(parts) >= 2:
                code_block = parts[1].strip()
                if code_block.startswith("json"):
                    code_block = code_block[4:].strip()
                text = code_block
        
        # Try to find valid JSON object
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
        if json_match:
            text = json_match.group(0)
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.debug(f"Failed to parse JSON: {text[:100]}")
            return None

    def _validate_action(self, action_name: str) -> bool:
        """Validate that action name is reasonable"""
        if not isinstance(action_name, str):
            return False
        if not action_name.isidentifier():
            return False
        if len(action_name) > 50:
            return False
        return True

    def infer_intent(self, command: str, context: dict | None = None, history: list | None = None) -> Intent:
        """
        Parse intent from command using AI brain.
        Includes error handling and validation.
        """
        try:
            response = self.brain.think(command, context=context, history=history)
            if not response:
                logger.warning("Empty response from brain")
                return Intent(
                    name="respond",
                    params={"text": "I didn't understand that."},
                    confidence=0.1,
                    raw_text=command,
                    source="model",
                )
            
            logger.debug(f"Brain response: {response[:100]}")
            data = self._extract_json(response)
            
            if data:
                action_name = data.get("action", "").strip()
                
                # Validate action name
                if not self._validate_action(action_name):
                    logger.warning(f"Invalid action name: {action_name}")
                    return Intent(
                        name="respond",
                        params={"text": response},
                        confidence=0.2,
                        raw_text=command,
                        source="model",
                        response_text=response,
                    )
                
                params = data.get("params", {})
                if not isinstance(params, dict):
                    params = {}
                
                logger.info(f"Intent parsed: {action_name}")
                return Intent(
                    name=action_name,
                    params=params,
                    confidence=0.5,
                    raw_text=command,
                    source="model",
                )
            
            # No JSON found, treat as conversational response
            logger.debug(f"No JSON in response, treating as conversation")
            return Intent(
                name="respond",
                params={"text": response},
                confidence=0.3,
                raw_text=command,
                source="model",
                response_text=response,
            )
        
        except Exception as e:
            logger.error(f"Error in infer_intent: {e}", exc_info=True)
            return Intent(
                name="respond",
                params={"text": "An error occurred processing your command."},
                confidence=0.0,
                raw_text=command,
                source="model",
            )

    def set_mode(self, mode: str) -> str:
        """Set AI mode (auto/local/gemini/groq)"""
        try:
            return self.brain.set_mode(mode)
        except Exception as e:
            logger.error(f"Error setting mode: {e}")
            return "error"
