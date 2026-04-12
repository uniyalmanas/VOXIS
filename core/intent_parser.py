import re

from model_router import ModelRouter
from state import Intent, RuntimeState


class IntentParser:
    def __init__(self, state: RuntimeState):
        self.state = state
        self.model_router = ModelRouter()
        self.quick_replies = {
            "hello": "Hello. How can I help?",
            "hi": "Hi. What would you like me to do?",
            "hey": "Yes?",
            "how are you": "I'm ready and working with you.",
            "who are you": "I'm VOXIS, your desktop copilot.",
            "thank you": "You're welcome.",
            "thanks": "You're welcome.",
            "good morning": "Good morning. I'm ready.",
            "good night": "Good night.",
            "namaste": "Namaste. Main ready hoon.",
            "kaise ho": "Main theek hoon. Bataiye, kya karna hai?",
            "tum kaun ho": "Main VOXIS hoon, aapka desktop copilot.",
            "shukriya": "Aapka swagat hai.",
        }

        self.direct_commands = {
            "mute": Intent(name="mute", confidence=1.0),
            "unmute": Intent(name="mute", confidence=1.0),
            "screenshot": Intent(name="take_screenshot", confidence=1.0),
            "take screenshot": Intent(name="take_screenshot", confidence=1.0),
            "capture screen": Intent(name="take_screenshot", confidence=1.0),
            "scroll up": Intent(name="scroll", params={"amount": 5}, confidence=1.0),
            "scroll down": Intent(name="scroll", params={"amount": -5}, confidence=1.0),
            "page up": Intent(name="hotkey", params={"keys": ["pageup"]}, confidence=1.0),
            "page down": Intent(name="hotkey", params={"keys": ["pagedown"]}, confidence=1.0),
            "go to top": Intent(name="hotkey", params={"keys": ["ctrl", "home"]}, confidence=1.0),
            "go to bottom": Intent(name="hotkey", params={"keys": ["ctrl", "end"]}, confidence=1.0),
            "close": Intent(name="hotkey", params={"keys": ["alt", "f4"], "confirmation": "Closing window"}, confidence=1.0),
            "close window": Intent(name="hotkey", params={"keys": ["alt", "f4"], "confirmation": "Closing window"}, confidence=1.0),
            "minimize": Intent(name="hotkey", params={"keys": ["win", "down"]}, confidence=1.0),
            "maximize": Intent(name="hotkey", params={"keys": ["win", "up"]}, confidence=1.0),
            "show desktop": Intent(name="hotkey", params={"keys": ["win", "d"]}, confidence=1.0),
            "task view": Intent(name="hotkey", params={"keys": ["win", "tab"]}, confidence=1.0),
            "switch app": Intent(name="hotkey", params={"keys": ["alt", "tab"]}, confidence=1.0),
            "switch window": Intent(name="hotkey", params={"keys": ["alt", "tab"]}, confidence=1.0),
            "lock screen": Intent(name="hotkey", params={"keys": ["win", "l"]}, confidence=1.0),
            "new tab": Intent(name="hotkey", params={"keys": ["ctrl", "t"]}, confidence=1.0),
            "close tab": Intent(name="hotkey", params={"keys": ["ctrl", "w"]}, confidence=1.0),
            "next tab": Intent(name="hotkey", params={"keys": ["ctrl", "tab"]}, confidence=1.0),
            "previous tab": Intent(name="hotkey", params={"keys": ["ctrl", "shift", "tab"]}, confidence=1.0),
            "reopen tab": Intent(name="hotkey", params={"keys": ["ctrl", "shift", "t"]}, confidence=1.0),
            "refresh": Intent(name="hotkey", params={"keys": ["ctrl", "r"]}, confidence=1.0),
            "reload": Intent(name="hotkey", params={"keys": ["ctrl", "r"]}, confidence=1.0),
            "go back": Intent(name="hotkey", params={"keys": ["alt", "left"]}, confidence=1.0),
            "go forward": Intent(name="hotkey", params={"keys": ["alt", "right"]}, confidence=1.0),
            "copy": Intent(name="hotkey", params={"keys": ["ctrl", "c"]}, confidence=1.0),
            "paste": Intent(name="hotkey", params={"keys": ["ctrl", "v"]}, confidence=1.0),
            "cut": Intent(name="hotkey", params={"keys": ["ctrl", "x"]}, confidence=1.0),
            "select all": Intent(name="hotkey", params={"keys": ["ctrl", "a"]}, confidence=1.0),
            "undo": Intent(name="hotkey", params={"keys": ["ctrl", "z"]}, confidence=1.0),
            "redo": Intent(name="hotkey", params={"keys": ["ctrl", "y"]}, confidence=1.0),
            "save": Intent(name="hotkey", params={"keys": ["ctrl", "s"]}, confidence=1.0),
            "find": Intent(name="hotkey", params={"keys": ["ctrl", "f"]}, confidence=1.0),
            "zoom in": Intent(name="hotkey", params={"keys": ["ctrl", "+"]}, confidence=1.0),
            "zoom out": Intent(name="hotkey", params={"keys": ["ctrl", "-"]}, confidence=1.0),
            "what's on my screen": Intent(name="read_screen", confidence=1.0),
            "read my screen": Intent(name="read_screen", confidence=1.0),
            "what do you see": Intent(name="read_screen", confidence=1.0),
            "summarize screen": Intent(name="read_screen", confidence=1.0),
            "system information": Intent(name="system_info", confidence=1.0),
            "my system information": Intent(name="system_info", confidence=1.0),
            "my laptop information": Intent(name="system_info", confidence=1.0),
            "about my laptop": Intent(name="system_info", confidence=1.0),
            "about my system": Intent(name="system_info", confidence=1.0),
            "what am i using": Intent(name="system_info", confidence=1.0),
            "switch to local": Intent(name="switch_model", params={"mode": "private"}, confidence=1.0),
            "use local ai": Intent(name="switch_model", params={"mode": "private"}, confidence=1.0),
            "use llama": Intent(name="switch_model", params={"mode": "private"}, confidence=1.0),
            "switch to gemini": Intent(name="switch_model", params={"mode": "gemini"}, confidence=1.0),
            "use gemini": Intent(name="switch_model", params={"mode": "gemini"}, confidence=1.0),
            "switch to groq": Intent(name="switch_model", params={"mode": "groq"}, confidence=1.0),
            "switch to grock": Intent(name="switch_model", params={"mode": "groq"}, confidence=1.0),
            "use groq": Intent(name="switch_model", params={"mode": "groq"}, confidence=1.0),
            "use grock": Intent(name="switch_model", params={"mode": "groq"}, confidence=1.0),
            "switch to auto": Intent(name="switch_model", params={"mode": "auto"}, confidence=1.0),
            "auto mode": Intent(name="switch_model", params={"mode": "auto"}, confidence=1.0),
            "switch to hindi": Intent(name="switch_language", params={"primary": "hi-IN", "fallback": "en-IN", "name": "Hindi"}, confidence=1.0),
            "switch to english": Intent(name="switch_language", params={"primary": "en-IN", "fallback": "en-US", "name": "English"}, confidence=1.0),
            "hindi mode": Intent(name="switch_language", params={"primary": "hi-IN", "fallback": "en-IN", "name": "Hindi"}, confidence=1.0),
            "english mode": Intent(name="switch_language", params={"primary": "en-IN", "fallback": "en-US", "name": "English"}, confidence=1.0),
            "volume up": Intent(name="set_volume", params={"direction": "up", "steps": 10}, confidence=1.0),
            "volume down": Intent(name="set_volume", params={"direction": "down", "steps": 10}, confidence=1.0),
            "volume badha": Intent(name="set_volume", params={"direction": "up", "steps": 10}, confidence=1.0),
            "volume kam karo": Intent(name="set_volume", params={"direction": "down", "steps": 10}, confidence=1.0),
            "awaaz badha": Intent(name="set_volume", params={"direction": "up", "steps": 10}, confidence=1.0),
            "awaaz kam karo": Intent(name="set_volume", params={"direction": "down", "steps": 10}, confidence=1.0),
        }
        self.known_apps = {
            "youtube", "linkedin", "gmail", "google", "github", "twitter",
            "whatsapp", "instagram", "netflix", "spotify", "notepad",
            "calculator", "calc", "camera", "settings", "vs code", "code",
            "file explorer", "task manager",
        }
        self.app_aliases = {
            "कैमरा": "camera",
            "camera": "camera",
            "कैलकुलेटर": "calculator",
            "calculator": "calculator",
            "calc": "calculator",
            "नोटपैड": "notepad",
            "notepad": "notepad",
            "सेटिंग्स": "settings",
            "settings": "settings",
            "यूट्यूब": "youtube",
            "youtube": "youtube",
            "गूगल": "google",
            "google": "google",
            "जीमेल": "gmail",
            "gmail": "gmail",
            "व्हाट्सएप": "whatsapp",
            "whatsapp": "whatsapp",
            "इंस्टाग्राम": "instagram",
            "instagram": "instagram",
            "स्पॉटिफाई": "spotify",
            "spotify": "spotify",
            "फाइल एक्सप्लोरर": "file explorer",
            "explorer": "file explorer",
            "टास्क मैनेजर": "task manager",
            "कोड": "code",
            "वीएस कोड": "vs code",
        }

    def parse(self, command: str) -> Intent:
        text = command.strip().lower()

        quick_reply = self._quick_reply(text)
        if quick_reply:
            return Intent(
                name="respond",
                params={"text": quick_reply},
                confidence=1.0,
                raw_text=command,
                source="rule",
                response_text=quick_reply,
            )

        for phrase, intent in self.direct_commands.items():
            if phrase in text:
                return Intent(
                    name=intent.name,
                    params=dict(intent.params),
                    confidence=intent.confidence,
                    raw_text=command,
                    source="rule",
                )

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

        search_match = re.search(r"^(search|google)\s+(.+)$", text)
        if search_match:
            return Intent(
                name="search_web",
                params={"query": search_match.group(2).strip(), "platform": "google"},
                confidence=0.95,
                raw_text=command,
                source="rule",
            )

        youtube_search_match = re.search(r"^(search youtube for|play)\s+(.+)$", text)
        if youtube_search_match:
            return Intent(
                name="search_web",
                params={"query": youtube_search_match.group(2).strip(), "platform": "youtube"},
                confidence=0.95,
                raw_text=command,
                source="rule",
            )

        calc_intent = self._parse_math_intent(text, command)
        if calc_intent:
            return calc_intent

        if self._is_system_info_query(text):
            return Intent(
                name="system_info",
                confidence=0.95,
                raw_text=command,
                source="rule",
            )

        model_switch_intent = self._parse_model_switch(text, command)
        if model_switch_intent:
            return model_switch_intent

        model_intent = self.model_router.infer_intent(
            command,
            context={
                "active_app": self.state.context.active_app or "",
                "last_command": self.state.context.last_command,
                "last_intent": self.state.context.last_intent,
                "last_action": self.state.context.last_action,
                "last_result": self.state.context.last_result,
                "primary_language": self.state.primary_language,
            },
        )
        if model_intent.name == "open_app":
            model_intent.params["app_name"] = self._normalize_app_name(
                model_intent.params.get("app_name", "")
            )
        model_intent.raw_text = command
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
        patterns = {
            "private": [
                "switch to local",
                "go local",
                "use local ai",
                "use local model",
                "switch to llama",
                "use llama",
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

    def _normalize_app_name(self, app_name: str) -> str:
        cleaned = app_name.strip().lower()
        for alias, canonical in self.app_aliases.items():
            if alias.lower() == cleaned:
                return canonical
        return cleaned

    def _quick_reply(self, text: str) -> str:
        if text in self.quick_replies:
            return self.quick_replies[text]

        if len(text.split()) <= 4:
            for phrase, reply in self.quick_replies.items():
                if text.startswith(phrase) or phrase in text:
                    return reply

        return ""
