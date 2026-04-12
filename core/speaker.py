import queue
import threading
from typing import Any

import pyttsx3


class Speaker:
    def __init__(self, rate: int, volume: float):
        self.rate = rate
        self.volume = volume
        self.current_language = "en-IN"
        self._queue: queue.Queue[tuple[str, Any]] = queue.Queue()
        self._ready = threading.Event()
        self._voice_names: list[str] = []
        self.cues_enabled = False
        self._worker = threading.Thread(
            target=self._run,
            daemon=True,
            name="VoxisSpeaker",
        )
        self._worker.start()
        self._ready.wait(timeout=5)
        self.set_language(self.current_language)

    def speak(self, text: str) -> None:
        if not text:
            return

        print(f"VOXIS: {text}")
        self._queue.put(("speak", text))

    def set_language(self, language: str) -> None:
        self.current_language = language
        self._queue.put(("language", language))

    def available_voice_names(self) -> list[str]:
        return list(self._voice_names)

    def cue(self, name: str = "listen") -> None:
        if not self.cues_enabled:
            return

        try:
            import winsound

            patterns = {
                "wake": (880, 120),
                "listen": (660, 100),
                "done": (520, 120),
            }
            frequency, duration = patterns.get(name, patterns["listen"])
            winsound.Beep(frequency, duration)
        except Exception:
            print(f"[cue:{name}]")

    def _run(self) -> None:
        try:
            engine = pyttsx3.init(driverName="sapi5")
        except Exception:
            engine = pyttsx3.init()

        engine.setProperty("rate", self.rate)
        engine.setProperty("volume", self.volume)
        self._voice_names = [
            str(getattr(voice, "name", "")).strip()
            for voice in (engine.getProperty("voices") or [])
            if str(getattr(voice, "name", "")).strip()
        ]
        self._ready.set()

        while True:
            kind, payload = self._queue.get()
            try:
                if kind == "language":
                    self._apply_language(engine, payload)
                elif kind == "speak":
                    engine.say(payload)
                    engine.runAndWait()
            except Exception as exc:
                print(f"[speaker_error] {kind}: {exc}")
            finally:
                self._queue.task_done()

    def _apply_language(self, engine, language: str) -> None:
        voices = engine.getProperty("voices") or []
        preferred_terms = (
            ["hi-in", "hindi", "heera", "hemant", "kalpana", "india"]
            if language.startswith("hi")
            else ["english", "zira", "david", "mark", "hazel"]
        )

        for voice in voices:
            haystack = " ".join([
                str(getattr(voice, "id", "")).lower(),
                str(getattr(voice, "name", "")).lower(),
                str(getattr(voice, "languages", "")).lower(),
            ])
            if any(term in haystack for term in preferred_terms):
                engine.setProperty("voice", voice.id)
                return
