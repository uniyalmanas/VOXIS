import os
import time
from collections import deque
import importlib.util

from google import genai
from groq import Groq
import ollama


sys_path = os.path.join(os.path.dirname(__file__), "..", "config", "settings.py")
spec = importlib.util.spec_from_file_location("settings", sys_path)
settings = importlib.util.module_from_spec(spec)
spec.loader.exec_module(settings)


class AIBrain:
    def __init__(self):
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
        self.gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.local_model = settings.LOCAL_MODEL
        self.mode = self._normalize_mode(settings.AI_MODE)
        self.conversation_history = deque(maxlen=10)
        self.local_status = "unchecked"
        self._last_local_check_ts = 0.0
        self._local_check_interval_seconds = 8.0

        self.system_prompt = """
You are VOXIS, a desktop AI collaborator.
Respond in one of two ways:

1. For computer actions: pure JSON only
{"action": "action_name", "params": {}}

2. For conversation: a short natural reply

Available actions:
- open_app: {"app_name": "name"}
- compose_email: {"to": "person@example.com", "subject": "subject", "body": "draft body"}
- search_web: {"query": "text", "platform": "google/youtube"}
- calculate: {"expression": "23 + 45"}
- switch_model: {"mode": "auto/private/gemini/groq"}
- set_volume: {"direction": "up/down", "steps": 10}
- mute
- scroll: {"amount": 5}
- hotkey: {"keys": ["ctrl", "t"]}
- press_key: {"key": "enter"}
- type_text: {"text": "text to type"}
- take_screenshot
- read_screen
- switch_language: {"primary": "hi-IN", "fallback": "en-IN", "name": "Hindi"}
- respond: {"text": "reply to user"}
- unknown

Rules:
- When the user asks for a computer action, output JSON only.
- For email requests, prepare drafts with compose_email; do not claim the email was sent.
- Use the provided desktop context for follow-up commands.
- Reply in the user's active language when speaking naturally.
- Be concise and practical.
"""
        print("VOXIS AI Brain Runtime - Initialized")
        print(f"Mode: {self.mode.upper()}")

    def _normalize_mode(self, mode: str | None) -> str:
        normalized = (mode or "auto").strip().lower()
        aliases = {
            "private": "local",
            "llama": "local",
            "llama3": "local",
            "grock": "groq",
            "speed": "groq",
        }
        return aliases.get(normalized, normalized)

    def _check_local_available(self) -> bool:
        now = time.time()

        if self.local_status == "available" and (now - self._last_local_check_ts) < self._local_check_interval_seconds:
            return True
        if self.local_status.startswith("unavailable") and (now - self._last_local_check_ts) < self._local_check_interval_seconds:
            return False

        try:
            ollama.list()
            self.local_status = "available"
            self._last_local_check_ts = now
            return True
        except Exception as exc:
            self.local_status = f"unavailable: {exc}"
            self._last_local_check_ts = now
            print(f"Local unavailable: {exc}")
            return False

    def _pick_model(self, command):
        if self.mode != "auto":
            return self.mode

        command_lower = command.lower()
        private_keywords = [
            "private", "secret", "personal",
            "password", "bank", "offline",
            "don't send", "local only",
        ]
        hindi_keywords = [
            "karo", "kro", "khol", "band karo",
            "chalao", "likho", "batao",
            "mera", "meri", "yaar", "bhai",
            "aur", "nahi", "haan", "theek",
            "youtube khol", "google khol",
            "awaaz", "volume badha", "volume ghata",
        ]
        complex_keywords = [
            "write", "explain", "summarize",
            "help me", "create", "generate",
            "analyze", "debug", "plan",
            "what is", "how to", "why",
        ]

        if any(word in command_lower for word in private_keywords):
            print("Private -> Local")
            return "local"
        if any(word in command_lower for word in hindi_keywords):
            print("Hindi -> Gemini")
            return "gemini"
        if any(word in command_lower for word in complex_keywords):
            print("Complex -> Gemini")
            return "gemini"

        print("Fast -> Groq")
        return "groq"

    def _build_messages(self, command, context=None, history=None):
        messages = [{"role": "system", "content": self.system_prompt}]

        if context:
            messages.append({
                "role": "system",
                "content": (
                    "Current desktop context:\n"
                    f"- active_app: {context.get('active_app', '')}\n"
                    f"- last_command: {context.get('last_command', '')}\n"
                    f"- last_intent: {context.get('last_intent', '')}\n"
                    f"- last_action: {context.get('last_action', '')}\n"
                    f"- last_result: {context.get('last_result', '')}\n"
                    f"- primary_language: {context.get('primary_language', '')}"
                ),
            })

        if history:
            messages.extend(history[-6:])
        else:
            messages.extend(list(self.conversation_history))

        messages.append({"role": "user", "content": command})
        return messages

    def _think_groq(self, command, context=None, history=None, allow_fallback=True):
        """Try Groq with automatic fallback to local on network error"""
        try:
            print(f"[AIBrain] Trying Groq...")
            messages = self._build_messages(command, context=context, history=history)
            response = self.groq_client.chat.completions.create(
                model=getattr(settings, "GROQ_MODEL", "llama-3.3-70b-versatile"),
                messages=messages,
                max_tokens=150,
                temperature=0.1,
            )
            print(f"[AIBrain] Groq succeeded")
            return response.choices[0].message.content.strip()
        except Exception as exc:
            error_msg = str(exc).lower()
            print(f"[AIBrain] Groq unavailable: {exc}")
            
            if allow_fallback:
                # Network errors -> try local first (offline-friendly)
                if any(term in error_msg for term in ["connection", "timeout", "network", "11001"]):
                    print(f"[AIBrain] Network error detected -> trying Local AI")
                    local_response = self._think_local(command, context=context, history=history, allow_fallback=False)
                    if not local_response.startswith('{"action": "respond"') or "unavailable" not in local_response:
                        return local_response
                
                # Other errors -> try Gemini
                print(f"[AIBrain] Groq unavailable -> trying Gemini")
                return self._think_gemini(command, context=context, history=history, allow_fallback=False)
            
            return '{"action": "respond", "params": {"text": "All AI models are unavailable right now."}}'

    def _think_gemini(self, command, context=None, history=None, allow_fallback=True):
        """Try Gemini with automatic fallback to local on network error"""
        try:
            print(f"[AIBrain] Trying Gemini...")
            prompt_parts = [self.system_prompt]
            if context:
                prompt_parts.append(
                    "Current desktop context:\n"
                    f"- active_app: {context.get('active_app', '')}\n"
                    f"- last_command: {context.get('last_command', '')}\n"
                    f"- last_intent: {context.get('last_intent', '')}\n"
                    f"- last_action: {context.get('last_action', '')}\n"
                    f"- last_result: {context.get('last_result', '')}\n"
                    f"- primary_language: {context.get('primary_language', '')}"
                )
            if history:
                prompt_parts.append(
                    "Recent conversation:\n" + "\n".join(
                        f"{item.get('role', 'user')}: {item.get('content', '')}"
                        for item in history[-6:]
                    )
                )
            prompt_parts.append(f"User: {command}")

            response = self.gemini_client.models.generate_content(
                model=getattr(settings, "GEMINI_MODEL", "gemini-2.0-flash"),
                contents="\n\n".join(prompt_parts),
            )
            print(f"[AIBrain] Gemini succeeded")
            return response.text.strip()
        except Exception as exc:
            error_msg = str(exc).lower()
            print(f"[AIBrain] Gemini unavailable: {exc}")
            
            if allow_fallback:
                # Network errors -> try local first
                if any(term in error_msg for term in ["connection", "timeout", "network", "11001", "getaddrinfo"]):
                    print(f"[AIBrain] Network error detected -> trying Local AI")
                    local_response = self._think_local(command, context=context, history=history, allow_fallback=False)
                    if not local_response.startswith('{"action": "respond"') or "unavailable" not in local_response:
                        return local_response
                
                # Other errors -> try Groq as last resort
                print(f"[AIBrain] Gemini unavailable -> trying Groq")
                return self._think_groq(command, context=context, history=history, allow_fallback=False)
            
            return '{"action": "respond", "params": {"text": "All AI models are unavailable right now."}}'

    def _think_local(self, command, context=None, history=None, allow_fallback=True):
        """Try local Ollama with graceful error handling"""
        try:
            print(f"[AIBrain] Trying Local AI...")
            if not self._check_local_available():
                raise RuntimeError(self.local_status)
            messages = self._build_messages(command, context=context, history=history)
            response = ollama.chat(
                model=self.local_model,
                messages=messages,
            )
            self.local_status = "available"
            print(f"[AIBrain] Local AI succeeded")
            return response["message"]["content"].strip()
        except Exception as exc:
            print(f"[AIBrain] Local unavailable: {exc}")
            if allow_fallback:
                print(f"[AIBrain] Local unavailable -> trying Groq")
                return self._think_groq(command, context=context, history=history, allow_fallback=True)
            return '{"action": "respond", "params": {"text": "Local AI is unavailable. Please check your Ollama installation."}}'

    def think(self, command, context=None, history=None):
        """
        Think about a command using the best available AI model.
        Automatic fallback chain:
        1. Try selected model (auto-picked or user-set)
        2. If network error -> try Local AI
        3. If local unavailable -> try other cloud models
        """
        try:
            model = self._normalize_mode(self._pick_model(command))
            print(f"[AIBrain] Selected model: {model}")

            if model in {"groq", "speed"}:
                reply = self._think_groq(command, context=context, history=history, allow_fallback=True)
            elif model == "gemini":
                reply = self._think_gemini(command, context=context, history=history, allow_fallback=True)
            else:  # "local" or unknown
                reply = self._think_local(command, context=context, history=history, allow_fallback=True)

            self.conversation_history.append({"role": "user", "content": command})
            self.conversation_history.append({"role": "assistant", "content": reply})
            return reply
        except Exception as exc:
            print(f"[AIBrain] Fatal error: {exc}")
            return '{"action": "respond", "params": {"text": "I encountered an error processing your command."}}'

    def set_mode(self, mode):
        normalized = self._normalize_mode(mode)
        valid_modes = ["auto", "local", "gemini", "groq"]
        if normalized in valid_modes:
            self.mode = normalized
            print(f"Mode: {normalized.upper()}")
            return f"Switched to {normalized} mode"
        return "Invalid mode"
