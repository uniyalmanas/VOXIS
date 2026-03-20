import os
import json
import re
from collections import deque
from groq import Groq
from google import genai
import ollama

# Load config
sys_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'settings.py')
import importlib.util
spec = importlib.util.spec_from_file_location("settings", sys_path)
settings = importlib.util.module_from_spec(spec)
spec.loader.exec_module(settings)

class AIBrain:
    def __init__(self):
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
        self.gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.local_model = settings.LOCAL_MODEL
        self.mode = settings.AI_MODE
        self.conversation_history = deque(maxlen=10)

        self.system_prompt = """
You are VOXIS, a silent AI assistant that controls a computer.
Respond ONLY in one of two ways:

1. For computer actions — pure JSON only:
{"action": "action_name", "params": {}}

2. For conversation — natural short response
Maximum 2 sentences. Be warm and friendly.

Available actions:
- open_app: {"app_name": "name"}
- search: {"query": "text", "platform": "google/youtube"}
- volume_up, volume_down, mute
- scroll_up, scroll_down
- close_window, take_screenshot
- new_tab, close_tab
- unknown

Examples:
"open youtube" → {"action": "open_app", "params": {"app_name": "youtube"}}
"play lofi music" → {"action": "search", "params": {"query": "lofi music", "platform": "youtube"}}
"how are you" → "I'm doing great! Ready to help."
"YouTube khol do" → {"action": "open_app", "params": {"app_name": "youtube"}}

CRITICAL: For actions output ONLY JSON. Nothing else. No labels.
"""
        print("VOXIS AI Brain - Initialized ✅")
        print(f"Mode: {self.mode.upper()}")

    def _pick_model(self, command):
        """AUTO mode — picks best model for command"""
        if self.mode != "auto":
            return self.mode

        # Private keywords → always local
        private_keywords = [
            "private", "secret", "personal",
            "password", "bank", "offline",
            "don't send", "local only"
        ]

        # Hindi keywords → must be clearly Hindi
        # Removed short words like "do", "de", "lo", "le"
        # that match common English words
        hindi_keywords = [
            "karo", "kro", "khol", "band karo",
            "chalao", "likho", "batao",
            "mera", "meri", "yaar", "bhai",
            "aur", "nahi", "haan", "theek",
            "youtube khol", "google khol",
            "awaaz", "volume badha", "volume ghata"
        ]

        # Complex keywords → Gemini
        complex_keywords = [
            "write", "explain", "summarize",
            "help me", "create", "generate",
            "analyze", "debug", "plan",
            "what is", "how to", "why"
        ]

        command_lower = command.lower()

        # Private → local LLaMA 3
        if any(word in command_lower for word in private_keywords):
            print("🔒 Private → Local LLaMA 3")
            return "private"

        # Hindi → Gemini
        if any(word in command_lower for word in hindi_keywords):
            print("🇮🇳 Hindi → Gemini")
            return "gemini"

        # Complex → Gemini
        if any(word in command_lower for word in complex_keywords):
            print("🧠 Complex → Gemini")
            return "gemini"

        # Default → Groq (fastest)
        print("⚡ Groq")
        return "groq"

    def _think_groq(self, command):
        """Fast responses via Groq"""
        try:
            messages = [
                {"role": "system", "content": self.system_prompt}
            ] + list(self.conversation_history) + [
                {"role": "user", "content": command}
            ]
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                max_tokens=150,
                temperature=0.1
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"⚠️ Groq unavailable → Local")
            return self._think_local(command)

    def _think_gemini(self, command):
        """Smart responses via Gemini — better Hindi"""
        try:
            full_prompt = f"{self.system_prompt}\n\nUser: {command}"
            response = self.gemini_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=full_prompt
            )
            return response.text.strip()
        except Exception as e:
            print(f"⚠️ Gemini unavailable → Groq")
            return self._think_groq(command)

    def _think_local(self, command):
        """Private responses via local LLaMA 3"""
        try:
            messages = [
                {"role": "system", "content": self.system_prompt}
            ] + list(self.conversation_history) + [
                {"role": "user", "content": command}
            ]
            response = ollama.chat(
                model=self.local_model,
                messages=messages
            )
            return response['message']['content'].strip()
        except Exception as e:
            print(f"⚠️ Local unavailable")
            return '{"action": "unknown", "params": {}}'

    def think(self, command):
        """Main entry — AUTO picks best model"""
        try:
            model = self._pick_model(command)

            if model == "groq" or model == "speed":
                reply = self._think_groq(command)
            elif model == "gemini":
                reply = self._think_gemini(command)
            else:
                reply = self._think_local(command)

            self.conversation_history.append({
                "role": "user",
                "content": command
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": reply
            })

            return reply

        except Exception as e:
            print(f"⚠️ AI Brain Error")
            return '{"action": "unknown", "params": {}}'

    def set_mode(self, mode):
        """Switch AI mode"""
        valid_modes = ["auto", "speed", "private", "gemini"]
        if mode in valid_modes:
            self.mode = mode
            print(f"Mode: {mode.upper()} ✅")
            return f"Switched to {mode} mode"
        return "Invalid mode"

if __name__ == "__main__":
    brain = AIBrain()
    tests = [
        "open youtube",
        "how are you",
        "YouTube khol do",
        "what can you do for me",
        "play lofi music on youtube",
        "search latest AI news",
        "tell me a joke",
    ]
    for test in tests:
        print(f"\nYou: {test}")
        print(f"VOXIS: {brain.think(test)}")