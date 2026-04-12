import importlib.util
import os
import sys
import time

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
        self.follow_up_prompts = {
            "en": "I'm listening.",
            "hi": "Main sun raha hoon.",
        }

        print(f"Language: {self.primary_language} -> {self.fallback_language}")
        print("VOXIS Voice Runtime - Initialized")
        self.ui.set_status("Ready")
        self.ui.set_mode(getattr(self.orchestrator.parser.model_router.brain, "mode", "auto"))
        self.ui.set_language(self.primary_language)

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
        self.ui.add_assistant_message(text)
        self.speaker.speak(text)

    def listen(self) -> str:
        return self.listener.listen()

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
        response = self.orchestrator.handle_command(command)
        if response:
            self.speak(response)
        self.ui.set_status("Listening")

    def _conversation_prompt(self) -> str:
        if self.primary_language.startswith("hi"):
            return self.follow_up_prompts["hi"]
        return self.follow_up_prompts["en"]

    def _start_live_session(self) -> None:
        self.orchestrator.activate_conversation()
        self.ui.set_status("Live conversation active")
        self.speak("Yes?")

    def _extract_command_after_wake(self, audio: str) -> str:
        lowered = audio.lower()
        for wake_word in self.wake_words:
            wake_lower = wake_word.lower()
            if wake_lower in lowered:
                candidate = lowered.replace(wake_lower, "", 1).strip(" ,.-")
                if candidate:
                    return candidate
        return ""

    def _handle_live_turn(self, audio: str) -> None:
        if not audio:
            return

        print(f"Command: {audio}")
        self.process_command(audio)

    def run(self) -> None:
        self.speak("VOXIS is ready")
        print("Say 'Jarvis' to activate live mode")
        print(f"Languages: {self.primary_language} + {self.fallback_language}")
        self.ui.set_status("Listening for wake word")

        while True:
            print("Listening...")
            audio = self.listen()
            if audio:
                print(f"Heard: '{audio}'")
                self.ui.set_status("Heard input")

            if any(word in audio for word in self.wake_words):
                self._start_live_session()
                inline_command = self._extract_command_after_wake(audio)
                if inline_command:
                    self._handle_live_turn(inline_command)
                continue

            if self.orchestrator.is_conversation_active():
                if audio:
                    self._handle_live_turn(audio)
                else:
                    time.sleep(0.1)
                continue

            self.ui.set_status("Listening for wake word")
            time.sleep(0.1)


if __name__ == "__main__":
    engine = VoiceEngine()
    engine.run()
