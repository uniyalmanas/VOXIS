import re
import logging

from command_registry import CommandRegistry
from model_router import ModelRouter
from state import Intent, RuntimeState


logger = logging.getLogger("VOXIS.IntentParser")


class IntentParser:
    def __init__(self, state: RuntimeState):
        self.state = state
        self.model_router = ModelRouter()
        self.command_registry = CommandRegistry()
    
    def parse(self, command: str) -> Intent:
        """
        Parse a command into an intent using multiple strategies:
        1. Quick replies (instant responses)
        2. Direct commands (from registry)
        3. Special pattern matching (type, open, search, email, etc.)
        4. Model inference (AI-powered fallback)
        """
        if not command or not command.strip():
            logger.warning("Empty command")
            return Intent(name="unknown", confidence=0.0)
        
        text = command.strip().lower()

        type_match = re.search(r"^(type|dictate|insert|write this)\s+(.+)$", text)
        if type_match:
            return Intent(
                name="type_text",
                params={"text": type_match.group(2)},
                confidence=0.98,
                raw_text=command,
                source="rule",
            )
        
        # Try quick reply
        quick_reply = self.command_registry.get_quick_reply(text)
        if quick_reply:
            logger.debug(f"Quick reply matched: {text}")
            return Intent(
                name="respond",
                params={"text": quick_reply},
                confidence=1.0,
                raw_text=command,
                source="quick_reply",
                response_text=quick_reply,
            )
        
        # Try direct command lookup
        direct_intent = self.command_registry.get_direct_command(text)
        if direct_intent:
            logger.debug(f"Direct command matched: {text}")
            return direct_intent
        
        # Try press command
        press_match = re.search(r"^press\s+([a-z0-9 ]+)$", text)
        if press_match:
            key = self._normalize_key_name(press_match.group(1))
            if key:
                return Intent(
                    name="press_key",
                    params={"key": key},
                    confidence=0.96,
                    raw_text=command,
                    source="rule",
                )
        
        # Try email intent
        email_intent = self._parse_email_intent(text, command)
        if email_intent:
            return email_intent
        
        # Try open/launch app
        open_match = re.search(r"^(open|launch|start)\s+(.+)$", text)
        if open_match:
            app_name = self._normalize_app_name(open_match.group(2).strip())
            return Intent(
                name="open_app",
                params={"app_name": app_name},
                confidence=0.95,
                raw_text=command,
                source="rule",
            )
        
        # Try Hindi open pattern
        hindi_open_match = re.search(r"^(.+?)\s+(खोलो|खोल|चलाओ|चालू करो)$", text)
        if hindi_open_match:
            app_name = self._normalize_app_name(hindi_open_match.group(1).strip())
            return Intent(
                name="open_app",
                params={"app_name": app_name},
                confidence=0.96,
                raw_text=command,
                source="rule",
            )
        
        # Try search command
        search_match = re.search(r"^(search|google)\s+(.+)$", text)
        if search_match:
            return Intent(
                name="search_web",
                params={"query": search_match.group(2).strip(), "platform": "google"},
                confidence=0.95,
                raw_text=command,
                source="rule",
            )
        
        # Try YouTube search
        youtube_search_match = re.search(r"^(search youtube for|play)\s+(.+)$", text)
        if youtube_search_match:
            return Intent(
                name="search_web",
                params={"query": youtube_search_match.group(2).strip(), "platform": "youtube"},
                confidence=0.95,
                raw_text=command,
                source="rule",
            )
        
        # Try math intent
        calc_intent = self._parse_math_intent(text, command)
        if calc_intent:
            return calc_intent
        
        # Try system info query
        if self._is_system_info_query(text):
            return Intent(
                name="system_info",
                confidence=0.95,
                raw_text=command,
                source="rule",
            )
        
        # Try model switching
        model_switch_intent = self._parse_model_switch(text, command)
        if model_switch_intent:
            return model_switch_intent
        
        # Fall back to model inference with context
        logger.debug(f"Using model inference for: {text}")
        context = {
            "active_app": self.state.context.active_app or "",
            "last_command": self.state.context.last_command,
            "last_intent": self.state.context.last_intent,
            "last_action": self.state.context.last_action,
            "last_result": self.state.context.last_result,
            "primary_language": self.state.primary_language,
        }
        
        model_intent = self.model_router.infer_intent(command, context=context)
        
        # Normalize app name if it's an open_app intent
        if model_intent.name == "open_app":
            app_name = model_intent.params.get("app_name", "")
            model_intent.params["app_name"] = self._normalize_app_name(app_name)
        
        return model_intent

    def _parse_math_intent(self, text: str, raw_command: str) -> Intent | None:
        normalized = (
            text.replace("plus", "+")
            .replace("minus", "-")
            .replace("times", "*")
            .replace("multiplied by", "*")
            .replace("x", "*")
            .replace("divided by", "/")
            .replace("into", "*")
        )

        add_match = re.search(r"(add|sum|plus)\s+(\d+(?:\.\d+)?)\s+(and|with)?\s*(\d+(?:\.\d+)?)", text)
        if add_match:
            expression = f"{add_match.group(2)} + {add_match.group(4)}"
            return Intent(
                name="calculate",
                params={"expression": expression},
                confidence=0.96,
                raw_text=raw_command,
                source="rule",
            )

        expr_match = re.search(r"(-?\d+(?:\.\d+)?\s*[\+\-\*/]\s*-?\d+(?:\.\d+)?(?:\s*[\+\-\*/]\s*-?\d+(?:\.\d+)?)*)", normalized)
        if expr_match:
            return Intent(
                name="calculate",
                params={"expression": expr_match.group(1)},
                confidence=0.92,
                raw_text=raw_command,
                source="rule",
            )

        if self.state.context.active_app in {"calculator", "calc"}:
            numbers = re.findall(r"\d+(?:\.\d+)?", text)
            if len(numbers) >= 2:
                if "add" in text or "plus" in text:
                    expression = " + ".join(numbers[:2])
                elif "subtract" in text or "minus" in text:
                    expression = f"{numbers[0]} - {numbers[1]}"
                elif "multiply" in text or "times" in text:
                    expression = f"{numbers[0]} * {numbers[1]}"
                elif "divide" in text:
                    expression = f"{numbers[0]} / {numbers[1]}"
                else:
                    expression = ""

                if expression:
                    return Intent(
                        name="calculate",
                        params={"expression": expression},
                        confidence=0.8,
                        raw_text=raw_command,
                        source="context",
                    )

        return None

    def _is_system_info_query(self, text: str) -> bool:
        patterns = [
            "tell me about my laptop",
            "tell me about my system",
            "give me my system information",
            "give me system information",
            "what laptop am i using",
            "what system am i using",
            "what device am i using",
            "my laptop specs",
            "my system specs",
            "my computer specs",
        ]
        return any(pattern in text for pattern in patterns)

    def _parse_model_switch(self, text: str, raw_command: str) -> Intent | None:
        """Parse AI model switching commands"""
        patterns = {
            "local": [
                "switch to local",
                "go local",
                "use local ai",
                "use local model",
                "switch to llama",
                "use llama",
                "switch to private",
            ],
            "gemini": [
                "switch to gemini",
                "use gemini",
                "go to gemini",
            ],
            "groq": [
                "switch to groq",
                "switch to grock",
                "use groq",
                "use grock",
                "go to groq",
            ],
            "auto": [
                "switch to auto",
                "use auto mode",
                "go to auto mode",
                "automatic mode",
            ],
        }

        for mode, phrases in patterns.items():
            if any(phrase in text for phrase in phrases):
                return Intent(
                    name="switch_model",
                    params={"mode": mode},
                    confidence=0.95,
                    raw_text=raw_command,
                    source="rule",
                )

        return None

    def _parse_email_intent(self, text: str, raw_command: str) -> Intent | None:
        email_match = re.search(
            r"([\w.+-]+\s*@\s*[\w.-]+\s*\.\s*[a-z]{2,})",
            text,
        )
        if not email_match:
            return None

        if not any(word in text for word in ["email", "mail", "gmail", "send", "compose", "draft"]):
            return None

        recipient = self._normalize_email_address(email_match.group(1))
        before_email = text[:email_match.start()].strip(" ,.-")
        after_email = text[email_match.end():].strip(" ,.-")

        body = ""
        body_patterns = [
            r"(?:write this|saying|that|body|message)\s+(.+?)(?:\s+(?:and\s+)?(?:send|mail|email)\s+(?:it\s+)?(?:to|for)\s*$|$)",
            r"(?:send|mail|email)\s+(.+?)\s+(?:to|for)\s*$",
        ]
        for pattern in body_patterns:
            match = re.search(pattern, before_email)
            if match:
                body = match.group(1).strip(" ,.-")
                break

        if not body and after_email:
            after_match = re.search(r"^(?:saying|that|body|message)\s+(.+)$", after_email)
            if after_match:
                body = after_match.group(1).strip(" ,.-")

        subject = "Draft from VOXIS"
        subject_match = re.search(r"subject\s+(.+?)(?:\s+body\s+|\s+message\s+|$)", text)
        if subject_match:
            subject = subject_match.group(1).strip(" ,.-")

        return Intent(
            name="compose_email",
            params={"to": recipient, "subject": subject, "body": body},
            confidence=0.9,
            raw_text=raw_command,
            source="rule",
        )

    def _normalize_app_name(self, app_name: str) -> str:
        """Normalize app name using aliases and registry"""
        cleaned = app_name.strip().lower()
        
        # Try registry alias resolution
        resolved = self.command_registry.resolve_app_alias(cleaned)
        if resolved:
            return resolved
        
        return cleaned

    def _normalize_key_name(self, key_name: str) -> str:
        cleaned = key_name.strip().lower()
        aliases = {
            "enter": "enter",
            "return": "enter",
            "tab": "tab",
            "escape": "esc",
            "esc": "esc",
            "backspace": "backspace",
            "delete": "delete",
            "space": "space",
            "up": "up",
            "down": "down",
            "left": "left",
            "right": "right",
            "page up": "pageup",
            "page down": "pagedown",
            "home": "home",
            "end": "end",
        }
        return aliases.get(cleaned, "")

    def _normalize_email_address(self, email: str) -> str:
        """Normalize email address"""
        return re.sub(r"\s+", "", email.strip().lower())
