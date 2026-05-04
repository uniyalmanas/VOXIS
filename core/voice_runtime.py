import importlib.util
import os
import re
import sys
import threading
import time

# Load settings
sys_path = os.path.join(os.path.dirname(__file__), "..", "config", "settings.py")
spec = importlib.util.spec_from_file_location("settings", sys_path)
settings = importlib.util.module_from_spec(spec)
spec.loader.exec_module(settings)

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from listener import VoiceListener
from orchestrator import VoiceOrchestrator
from screen_vision import ScreenVision
from speaker import Speaker
from companion_window import CompanionWindow


class VoiceEngine:
    def __init__(self):
        self.primary_language = settings.PRIMARY_LANGUAGE
        self.fallback_language = settings.FALLBACK_LANGUAGE

        # Wake words used by the live conversation loop.
        self.wake_words = [
            "jarvis",
            "जार्विस",
            "hey jarvis",
            "हे जार्विस",
            "अरे जार्विस",
            "voxis",
            "वॉक्सिस",
        ]

        self.vision = None

        self.listener = VoiceListener(
            primary_language=self.primary_language,
            fallback_language=self.fallback_language,
        )

        self.ui = CompanionWindow()

        self.speaker = Speaker(
            rate=getattr(settings, "VOICE_SPEED", 175),
            volume=getattr(settings, "VOICE_VOLUME", 1.0),
        )
        self.speaker.set_language(self.primary_language)

        self.orchestrator = VoiceOrchestrator(self)
        self.ui.set_command_handler(self.process_command)

        self.follow_up_prompts = {
            "en": "I'm listening.",
            "hi": "Main sun raha hoon.",
        }
        self.require_wake_word = getattr(settings, "REQUIRE_WAKE_WORD", True)
        self._speech_lock = threading.RLock()
        self._last_speech_finished_ts = 0.0
        self._post_speech_pause_seconds = 0.25

        print(f"Language: {self.primary_language} -> {self.fallback_language}")
        print("VOXIS Voice Runtime - Initialized")

        self.ui.set_status("Ready")
        self.ui.set_mode(getattr(self.orchestrator.parser.model_router.brain, "mode", "auto"))
        self.ui.set_language(self.primary_language)

    # Robust wake detection.
    def is_wake_word(self, audio: str) -> bool:
        if not audio:
            return False

        triggers = {
            "jarvis",
            "jarv",
            "hey jar",
            "jervis",
            "service",
            "hey jarvis",
            "voxis",
            "vox is",
            "वॉक्सिस",
            "जार्विस",
            "हे जार्विस",
            "अरे जार्विस",
        }

        normalized = audio.lower().strip()
        words = set(re.findall(r"[\w']+", normalized))

        if words.intersection(triggers):
            return True

        return any(
            trigger in normalized
            for trigger in triggers
            if " " in trigger or not trigger.isascii()
        )

    def resolve_code_path(self) -> str:
        candidates = [
            "C:/Users/uniya/AppData/Local/Programs/Microsoft VS Code/Code.exe",
            os.path.expandvars(r"%LocalAppData%/Programs/Microsoft VS Code/Code.exe"),
        ]
        for candidate in candidates:
            normalized = os.path.normpath(candidate)
            if os.path.exists(normalized):
                return normalized
        return "code"

    def get_vision(self) -> ScreenVision:
        if self.vision is None:
            print("Loading screen vision...")
            self.vision = ScreenVision()
        return self.vision

    def speak(self, text: str) -> None:
        print(f"[voice] speak called: {text}")

        self.ui.add_assistant_message(text)

        with self._speech_lock:
            self.orchestrator.state.is_listening = False
            self.ui.set_status("Speaking...")

            try:
                self.speaker.speak(text)
                self.speaker.wait_until_idle(timeout=8)
            except Exception as e:
                print(f"[voice_error] speaker: {e}")
            finally:
                self._last_speech_finished_ts = time.time()
                self.orchestrator.state.is_listening = True
    
    def listen(self, timeout: float | None = None, phrase_time_limit: float | None = None) -> str:
        if not self.orchestrator.state.is_listening:
            return ""

        if time.time() - self._last_speech_finished_ts < self._post_speech_pause_seconds:
            return ""

        return self.listener.listen(timeout=timeout, phrase_time_limit=phrase_time_limit)

    def set_languages(self, primary: str, fallback: str) -> None:
        self.primary_language = primary
        self.fallback_language = fallback

        self.listener.set_languages(primary, fallback)
        self.speaker.set_language(primary)
        self.orchestrator.set_languages(primary, fallback)

        print(f"Language: {primary}")
        self.ui.set_language(primary)
        self.ui.set_status("Language updated")

    def set_model_mode(self, mode: str) -> None:
        self.ui.set_mode(mode)

    def process_command(self, command: str) -> None:
        self.ui.add_user_message(command)
        self.ui.set_status("Thinking...")

        try:
            response = self.orchestrator.handle_command(command)
        except Exception as e:
            print(f"[voice_error] orchestrator: {e}")
            response = "Something went wrong."

        if response:
            self.speak(response)

        self.ui.set_status("Listening")

    def _conversation_prompt(self) -> str:
        if self.primary_language.startswith("hi"):
            return self.follow_up_prompts["hi"]
        return self.follow_up_prompts["en"]

    def _start_live_session(self, prompt: bool = True) -> None:
        print("[voice] wake word detected")
        self.orchestrator.activate_conversation()
        self.ui.set_status("Live conversation active")
        if prompt:
            self.speak("Yes?")

    # Extract an inline command from input that includes the wake word.
    def _extract_command_after_wake(self, audio: str) -> str:
        if not audio:
            return ""

        lowered = audio.lower()

        triggers = [
            "hey jarvis",
            "jarvis",
            "hey jar",
            "jervis",
            "service",
            "jarv",
            "voxis",
            "vox is",
            "हे जार्विस",
            "अरे जार्विस",
            "जार्विस",
            "वॉक्सिस",
        ]

        for trigger in triggers:
            if trigger in lowered:
                return lowered.replace(trigger, "", 1).strip(" ,.-")

        return ""

    def _handle_live_turn(self, audio: str) -> None:
        if not audio:
            return

        print(f"[voice] command: {audio}")
        self.process_command(audio)

    def run(self) -> None:
        self.speak("VOXIS is ready")

        if self.require_wake_word:
            print("Say 'Jarvis' to activate live mode")
        else:
            print("Wake-free mode active. Speak a command directly.")
        print(f"Languages: {self.primary_language} + {self.fallback_language}")

        self.ui.set_status("Listening" if not self.require_wake_word else "Listening for wake word")

        while True:
            print("[voice] listening...")
            audio = self.listen(timeout=3.5, phrase_time_limit=6)

            if audio:
                print(f"[voice] heard: '{audio}'")
                self.ui.set_status("Heard input")
            else:
                print("[voice] no input detected")

            # Wake detection.
            if audio and self.is_wake_word(audio):
                inline_command = self._extract_command_after_wake(audio)
                self._start_live_session(prompt=not inline_command)
                if inline_command:
                    self._handle_live_turn(inline_command)

                continue

            # Conversation mode
            if self.orchestrator.is_conversation_active():
                if audio:
                    self._handle_live_turn(audio)
                else:
                    time.sleep(0.1)
                continue

            if audio and not self.require_wake_word:
                self._handle_live_turn(audio)
                continue

            self.ui.set_status("Listening for wake word" if self.require_wake_word else "Listening")
            time.sleep(0.1)


if __name__ == "__main__":
    engine = VoiceEngine()
    engine.run()
