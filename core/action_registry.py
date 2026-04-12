import datetime
import math
import os
import platform
import subprocess
import urllib.parse
import ctypes

import pyautogui

from state import Action


def _open_target(target: str) -> None:
    subprocess.Popen(["cmd", "/c", "start", "", target])


def _safe_eval_expression(expression: str) -> float:
    allowed = set("0123456789+-*/(). ")
    if any(ch not in allowed for ch in expression):
        raise ValueError("Unsupported math expression")

    return eval(expression, {"__builtins__": {}}, {"math": math})


class ActionRegistry:
    def __init__(self, voice_engine):
        self.voice_engine = voice_engine
        self.handlers = {
            "open_app": self.open_app,
            "search_web": self.search_web,
            "calculate": self.calculate,
            "system_info": self.system_info,
            "switch_model": self.switch_model,
            "set_volume": self.set_volume,
            "mute": self.mute,
            "take_screenshot": self.take_screenshot,
            "scroll": self.scroll,
            "hotkey": self.hotkey,
            "read_screen": self.read_screen,
            "switch_language": self.switch_language,
            "respond": self.respond,
            "unknown": self.unknown,
        }

    def execute(self, action: Action) -> dict:
        handler = self.handlers.get(action.name, self.unknown)
        return handler(action.params)

    def open_app(self, params: dict) -> dict:
        app = params.get("app_name", "").lower().strip()
        urls = {
            "youtube": "https://www.youtube.com",
            "linkedin": "https://www.linkedin.com",
            "gmail": "https://mail.google.com",
            "google": "https://www.google.com",
            "github": "https://www.github.com",
            "twitter": "https://www.twitter.com",
            "whatsapp": "https://web.whatsapp.com",
            "instagram": "https://www.instagram.com",
            "netflix": "https://www.netflix.com",
        }
        executables = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "calc": "calc.exe",
            "camera": "microsoft.windows.camera:",
            "settings": "ms-settings:",
            "file explorer": "explorer.exe",
            "task manager": "taskmgr.exe",
            "spotify": "spotify:",
        }
        aliases = {
            "vs code": self.voice_engine.resolve_code_path(),
            "vscode": self.voice_engine.resolve_code_path(),
            "code": self.voice_engine.resolve_code_path(),
        }

        if app in urls:
            _open_target(urls[app])
        elif app in executables:
            target = executables[app]
            if ":" in target:
                _open_target(target)
            else:
                subprocess.Popen(target)
        elif app in aliases and aliases[app]:
            subprocess.Popen(aliases[app])
        elif app:
            try:
                _open_target(app)
            except Exception:
                return {"speak_text": f"I could not open {app}."}

        return {"speak_text": f"Opening {app or 'application'}"}

    def search_web(self, params: dict) -> dict:
        query = params.get("query", "").strip()
        platform = params.get("platform", "google")
        query_encoded = urllib.parse.quote(query)

        if "youtube" in platform.lower():
            url = f"https://www.youtube.com/results?search_query={query_encoded}"
        else:
            url = f"https://www.google.com/search?q={query_encoded}"

        _open_target(url)
        return {"speak_text": f"Searching for {query}"}

    def calculate(self, params: dict) -> dict:
        expression = params.get("expression", "").strip()
        if not expression:
            return {"speak_text": "I need a math expression to calculate."}

        try:
            result = _safe_eval_expression(expression)
        except Exception:
            return {"speak_text": "I could not calculate that."}

        normalized = int(result) if float(result).is_integer() else result
        return {"speak_text": str(normalized), "text": str(normalized)}

    def system_info(self, params: dict) -> dict:
        details = self._collect_system_info()
        primary_language = getattr(self.voice_engine, "primary_language", "en-IN")

        if primary_language.startswith("hi"):
            summary = (
                f"Aap {details['machine']} use kar rahe hain. "
                f"Isme {details['os']}, {details['cpu']}, "
                f"lagbhag {details['ram_gb']} GB RAM aur {details['screen']} display hai."
            )
        else:
            summary = (
                f"You are using a {details['machine']} running {details['os']}. "
                f"It has {details['cpu']}, about {details['ram_gb']} GB RAM, "
                f"and a {details['screen']} display."
            )

        return {"speak_text": summary, "text": summary}

    def switch_model(self, params: dict) -> dict:
        requested_mode = params.get("mode", "auto").lower().strip()
        normalized_mode = {
            "private": "local",
            "local": "local",
            "llama": "local",
            "llama3": "local",
            "grock": "groq",
        }.get(requested_mode, requested_mode)

        message = self.voice_engine.orchestrator.parser.model_router.set_mode(normalized_mode)
        primary_language = getattr(self.voice_engine, "primary_language", "en-IN")

        if message == "Invalid mode":
            if primary_language.startswith("hi"):
                return {"speak_text": "Yeh AI mode supported nahi hai."}
            return {"speak_text": "That AI mode is not supported."}

        if primary_language.startswith("hi"):
            spoken_name = {
                "local": "local LLaMA",
                "gemini": "Gemini",
                "groq": "Groq",
                "auto": "auto",
            }.get(normalized_mode, normalized_mode)
            self.voice_engine.set_model_mode(normalized_mode)
            return {"speak_text": f"Ab main {spoken_name} mode use karunga."}

        self.voice_engine.set_model_mode(normalized_mode)
        return {"speak_text": message}

    def set_volume(self, params: dict) -> dict:
        direction = params.get("direction", "up")
        steps = int(params.get("steps", 10))
        key = "volumeup" if direction == "up" else "volumedown"
        for _ in range(max(1, steps)):
            pyautogui.press(key)
        return {"speak_text": f"Volume {direction}"}

    def mute(self, params: dict) -> dict:
        pyautogui.press("volumemute")
        return {"speak_text": "Muted"}

    def take_screenshot(self, params: dict) -> dict:
        folder = os.path.join(os.path.expanduser("~"), "Pictures")
        os.makedirs(folder, exist_ok=True)
        filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        path = os.path.join(folder, filename)
        pyautogui.screenshot(path)
        return {"speak_text": "Screenshot saved", "text": path}

    def scroll(self, params: dict) -> dict:
        amount = int(params.get("amount", 5))
        pyautogui.scroll(amount)
        return {"speak_text": ""}

    def hotkey(self, params: dict) -> dict:
        keys = params.get("keys", [])
        if isinstance(keys, list) and keys:
            pyautogui.hotkey(*keys)
        return {"speak_text": params.get("confirmation", "")}

    def read_screen(self, params: dict) -> dict:
        summary = self.voice_engine.get_vision().summarize_screen()
        return {"speak_text": summary, "text": summary}

    def switch_language(self, params: dict) -> dict:
        primary = params.get("primary", self.voice_engine.primary_language)
        fallback = params.get("fallback", self.voice_engine.fallback_language)
        name = params.get("name", "selected")
        self.voice_engine.set_languages(primary, fallback)
        return {"speak_text": f"Switched to {name} mode"}

    def respond(self, params: dict) -> dict:
        return {"speak_text": params.get("text", "")}

    def unknown(self, params: dict) -> dict:
        return {"speak_text": "Sorry, I didn't understand that"}

    def _collect_system_info(self) -> dict:
        uname = platform.uname()
        ram_gb = self._get_total_ram_gb()
        screen_width, screen_height = pyautogui.size()

        machine = "laptop or desktop computer"
        if "book" in uname.node.lower() or "laptop" in uname.node.lower():
            machine = "laptop"
        elif "portable" in uname.node.lower():
            machine = "laptop"

        os_name = f"{uname.system} {uname.release}"
        cpu = platform.processor() or f"{os.cpu_count()} core processor"

        return {
            "machine": machine,
            "os": os_name,
            "cpu": cpu,
            "ram_gb": ram_gb,
            "screen": f"{screen_width} by {screen_height}",
        }

    def _get_total_ram_gb(self) -> int:
        try:
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            memory_status = MEMORYSTATUSEX()
            memory_status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory_status))
            return round(memory_status.ullTotalPhys / (1024 ** 3))
        except Exception:
            return 0
