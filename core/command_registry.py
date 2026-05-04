"""
Command registry - centralized definition of all supported commands.
This replaces hardcoded dictionaries scattered across modules.
"""

from state import Intent


class CommandRegistry:
    """Manages all VOXIS commands and intents in one place"""
    
    def __init__(self):
        self.direct_commands = self._build_direct_commands()
        self.quick_replies = self._build_quick_replies()
        self.known_apps = self._build_known_apps()
        self.app_aliases = self._build_app_aliases()
    
    @staticmethod
    def _build_direct_commands() -> dict:
        """System commands with direct intent mapping"""
        return {
            # Volume control
            "mute": Intent(name="mute", confidence=1.0),
            "unmute": Intent(name="mute", confidence=1.0),
            "volume up": Intent(name="set_volume", params={"direction": "up", "steps": 10}, confidence=1.0),
            "volume down": Intent(name="set_volume", params={"direction": "down", "steps": 10}, confidence=1.0),
            "volume badha": Intent(name="set_volume", params={"direction": "up", "steps": 10}, confidence=1.0),
            "volume kam karo": Intent(name="set_volume", params={"direction": "down", "steps": 10}, confidence=1.0),
            "awaaz badha": Intent(name="set_volume", params={"direction": "up", "steps": 10}, confidence=1.0),
            "awaaz kam karo": Intent(name="set_volume", params={"direction": "down", "steps": 10}, confidence=1.0),
            
            # Screenshots
            "screenshot": Intent(name="take_screenshot", confidence=1.0),
            "take screenshot": Intent(name="take_screenshot", confidence=1.0),
            "capture screen": Intent(name="take_screenshot", confidence=1.0),
            
            # Scrolling
            "scroll up": Intent(name="scroll", params={"amount": 5}, confidence=1.0),
            "scroll down": Intent(name="scroll", params={"amount": -5}, confidence=1.0),
            "page up": Intent(name="hotkey", params={"keys": ["pageup"]}, confidence=1.0),
            "page down": Intent(name="hotkey", params={"keys": ["pagedown"]}, confidence=1.0),
            "go to top": Intent(name="hotkey", params={"keys": ["ctrl", "home"]}, confidence=1.0),
            "go to bottom": Intent(name="hotkey", params={"keys": ["ctrl", "end"]}, confidence=1.0),
            "upar jao": Intent(name="scroll", params={"amount": 5}, confidence=1.0),
            "neeche jao": Intent(name="scroll", params={"amount": -5}, confidence=1.0),
            
            # Window control
            "close": Intent(name="hotkey", params={"keys": ["alt", "f4"], "confirmation": "Closing window"}, confidence=1.0),
            "close window": Intent(name="hotkey", params={"keys": ["alt", "f4"], "confirmation": "Closing window"}, confidence=1.0),
            "minimize": Intent(name="hotkey", params={"keys": ["win", "down"]}, confidence=1.0),
            "maximize": Intent(name="hotkey", params={"keys": ["win", "up"]}, confidence=1.0),
            "show desktop": Intent(name="hotkey", params={"keys": ["win", "d"]}, confidence=1.0),
            "task view": Intent(name="hotkey", params={"keys": ["win", "tab"]}, confidence=1.0),
            "switch app": Intent(name="hotkey", params={"keys": ["alt", "tab"]}, confidence=1.0),
            "switch window": Intent(name="hotkey", params={"keys": ["alt", "tab"]}, confidence=1.0),
            "lock screen": Intent(name="hotkey", params={"keys": ["win", "l"]}, confidence=1.0),
            "band karo": Intent(name="hotkey", params={"keys": ["alt", "f4"], "confirmation": "Closing window"}, confidence=1.0),
            "chota karo": Intent(name="hotkey", params={"keys": ["win", "down"]}, confidence=1.0),
            "bada karo": Intent(name="hotkey", params={"keys": ["win", "up"]}, confidence=1.0),
            
            # Tabs
            "new tab": Intent(name="hotkey", params={"keys": ["ctrl", "t"]}, confidence=1.0),
            "close tab": Intent(name="hotkey", params={"keys": ["ctrl", "w"]}, confidence=1.0),
            "next tab": Intent(name="hotkey", params={"keys": ["ctrl", "tab"]}, confidence=1.0),
            "previous tab": Intent(name="hotkey", params={"keys": ["ctrl", "shift", "tab"]}, confidence=1.0),
            "reopen tab": Intent(name="hotkey", params={"keys": ["ctrl", "shift", "t"]}, confidence=1.0),
            "refresh": Intent(name="hotkey", params={"keys": ["ctrl", "r"]}, confidence=1.0),
            "reload": Intent(name="hotkey", params={"keys": ["ctrl", "r"]}, confidence=1.0),
            "go back": Intent(name="hotkey", params={"keys": ["alt", "left"]}, confidence=1.0),
            "go forward": Intent(name="hotkey", params={"keys": ["alt", "right"]}, confidence=1.0),
            
            # Editing
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
            
            # Text input
            "press enter": Intent(name="press_key", params={"key": "enter"}, confidence=1.0),
            "enter": Intent(name="press_key", params={"key": "enter"}, confidence=1.0),
            "new line": Intent(name="press_key", params={"key": "enter"}, confidence=1.0),
            "next line": Intent(name="press_key", params={"key": "enter"}, confidence=1.0),
            "press tab": Intent(name="press_key", params={"key": "tab"}, confidence=1.0),
            "tab": Intent(name="press_key", params={"key": "tab"}, confidence=1.0),
            "press escape": Intent(name="press_key", params={"key": "esc"}, confidence=1.0),
            "escape": Intent(name="press_key", params={"key": "esc"}, confidence=1.0),
            "backspace": Intent(name="press_key", params={"key": "backspace"}, confidence=1.0),
            "delete": Intent(name="press_key", params={"key": "delete"}, confidence=1.0),
            "space": Intent(name="press_key", params={"key": "space"}, confidence=1.0),
            
            # IDE/Editor
            "command palette": Intent(name="hotkey", params={"keys": ["ctrl", "shift", "p"], "confirmation": "Command palette"}, confidence=1.0),
            "open terminal": Intent(name="hotkey", params={"keys": ["ctrl", "`"], "confirmation": "Terminal"}, confidence=1.0),
            "toggle terminal": Intent(name="hotkey", params={"keys": ["ctrl", "`"], "confirmation": "Terminal"}, confidence=1.0),
            "format document": Intent(name="hotkey", params={"keys": ["shift", "alt", "f"], "confirmation": "Formatting"}, confidence=1.0),
            "comment line": Intent(name="hotkey", params={"keys": ["ctrl", "/"], "confirmation": "Comment toggled"}, confidence=1.0),
            "go to file": Intent(name="hotkey", params={"keys": ["ctrl", "p"], "confirmation": "Go to file"}, confidence=1.0),
            "quick open": Intent(name="hotkey", params={"keys": ["ctrl", "p"], "confirmation": "Quick open"}, confidence=1.0),
            
            # Screen reading
            "what's on my screen": Intent(name="read_screen", confidence=1.0),
            "read my screen": Intent(name="read_screen", confidence=1.0),
            "what do you see": Intent(name="read_screen", confidence=1.0),
            "summarize screen": Intent(name="read_screen", confidence=1.0),
            "screen dekho": Intent(name="read_screen", confidence=1.0),
            "screen batao": Intent(name="read_screen", confidence=1.0),
            
            # System info
            "system information": Intent(name="system_info", confidence=1.0),
            "my system information": Intent(name="system_info", confidence=1.0),
            "my laptop information": Intent(name="system_info", confidence=1.0),
            "about my laptop": Intent(name="system_info", confidence=1.0),
            "about my system": Intent(name="system_info", confidence=1.0),
            "what am i using": Intent(name="system_info", confidence=1.0),
            
            # Model switching
            "switch to local": Intent(name="switch_model", params={"mode": "local"}, confidence=1.0),
            "use local ai": Intent(name="switch_model", params={"mode": "local"}, confidence=1.0),
            "use llama": Intent(name="switch_model", params={"mode": "local"}, confidence=1.0),
            "switch to gemini": Intent(name="switch_model", params={"mode": "gemini"}, confidence=1.0),
            "use gemini": Intent(name="switch_model", params={"mode": "gemini"}, confidence=1.0),
            "switch to groq": Intent(name="switch_model", params={"mode": "groq"}, confidence=1.0),
            "switch to grock": Intent(name="switch_model", params={"mode": "groq"}, confidence=1.0),
            "use groq": Intent(name="switch_model", params={"mode": "groq"}, confidence=1.0),
            "use grock": Intent(name="switch_model", params={"mode": "groq"}, confidence=1.0),
            "switch to auto": Intent(name="switch_model", params={"mode": "auto"}, confidence=1.0),
            "auto mode": Intent(name="switch_model", params={"mode": "auto"}, confidence=1.0),
            
            # Language switching
            "switch to hindi": Intent(name="switch_language", params={"primary": "hi-IN", "fallback": "en-IN", "name": "Hindi"}, confidence=1.0),
            "switch to english": Intent(name="switch_language", params={"primary": "en-IN", "fallback": "en-US", "name": "English"}, confidence=1.0),
            "hindi mode": Intent(name="switch_language", params={"primary": "hi-IN", "fallback": "en-IN", "name": "Hindi"}, confidence=1.0),
            "english mode": Intent(name="switch_language", params={"primary": "en-IN", "fallback": "en-US", "name": "English"}, confidence=1.0),
        }
    
    @staticmethod
    def _build_quick_replies() -> dict:
        """Quick conversational replies"""
        return {
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
    
    @staticmethod
    def _build_known_apps() -> set:
        """Known application names"""
        return {
            "youtube", "linkedin", "gmail", "google", "github", "twitter",
            "whatsapp", "instagram", "netflix", "spotify", "notepad",
            "calculator", "calc", "camera", "settings", "vs code", "code",
            "file explorer", "task manager", "explorer",
        }
    
    @staticmethod
    def _build_app_aliases() -> dict:
        """App name aliases for multiple languages"""
        return {
            # Hindi aliases
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
    
    def get_direct_command(self, command_text: str) -> Intent | None:
        """Look up a direct command by text"""
        return self.direct_commands.get(command_text.lower().strip())
    
    def get_quick_reply(self, text: str) -> str | None:
        """Look up a quick reply by text"""
        return self.quick_replies.get(text.lower().strip())
    
    def is_known_app(self, app_name: str) -> bool:
        """Check if an app is in the known apps set"""
        return app_name.lower().strip() in self.known_apps
    
    def resolve_app_alias(self, alias: str) -> str | None:
        """Resolve an app alias to canonical name"""
        return self.app_aliases.get(alias.lower().strip())
