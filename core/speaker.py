import ctypes
import queue
import subprocess
import threading
from typing import Any

import pyttsx3


class Speaker:
    def __init__(self, rate: int, volume: float):
        self.rate = rate
        self.volume = volume
        self.current_language = "en-IN"
        self.cues_enabled = False
        self._voice_names: list[str] = []
        self._queue: queue.Queue[tuple[str, Any]] = queue.Queue()
        self._ready = threading.Event()
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

        print(f"[speaker] speak: {text}")
        self._queue.put(("speak", text))

    def wait_until_idle(self, timeout: float | None = None) -> None:
        if timeout is None:
            self._queue.join()
            return

        done = threading.Event()

        def _wait() -> None:
            self._queue.join()
            done.set()

        threading.Thread(target=_wait, daemon=True).start()
        done.wait(timeout=timeout)

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
        ctypes.windll.ole32.CoInitialize(None)
        engine = None
        self._voice_names = self._get_windows_voice_names()

        self._ready.set()

        try:
            while True:
                kind, payload = self._queue.get()
                try:
                    if kind == "language":
                        self.current_language = payload
                    elif kind == "speak":
                        self._speak_windows(str(payload))
                except Exception as exc:
                    print(f"[speaker_error] {kind}: {exc}")
                finally:
                    self._queue.task_done()
        finally:
            ctypes.windll.ole32.CoUninitialize()

    def _refresh_voice_names(self, engine) -> None:
        voices = engine.getProperty("voices") or []
        self._voice_names = [
            str(getattr(voice, "name", "")).strip()
            for voice in voices
            if str(getattr(voice, "name", "")).strip()
        ]

        print("[speaker] available voices:")
        for voice_name in self._voice_names:
            print(f" - {voice_name}")

    def _apply_language(self, engine, language: str) -> None:
        voices = engine.getProperty("voices") or []
        preferred_terms = (
            ["hi", "hindi", "india", "heera", "hemant", "kalpana"]
            if language.startswith("hi")
            else ["english", "en", "zira", "david", "hazel", "mark"]
        )

        for voice in voices:
            haystack = " ".join([
                str(getattr(voice, "id", "")).lower(),
                str(getattr(voice, "name", "")).lower(),
                str(getattr(voice, "languages", "")).lower(),
            ])

            if any(term in haystack for term in preferred_terms):
                engine.setProperty("voice", voice.id)
                print(f"[speaker] voice set: {voice.name}")
                return

        print("[speaker] no matching voice found, using default")

    def _speak_windows(self, text: str) -> None:
        escaped = text.replace("'", "''")
        voice_name = self._pick_windows_voice_name()
        rate = max(-10, min(10, int((self.rate - 175) / 15)))
        volume = max(0, min(100, int(self.volume * 100)))

        script = (
            "Add-Type -AssemblyName System.Speech; "
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$s.Volume = {volume}; "
            f"$s.Rate = {rate}; "
            f"try {{ $s.SelectVoice('{voice_name}') }} catch {{}}; "
            f"$s.Speak('{escaped}');"
        )

        try:
            subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    script,
                ],
                check=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except Exception as exc:
            print(f"[speaker_error] windows_fallback: {exc}")

    def _pick_windows_voice_name(self) -> str:
        available = [name.lower() for name in self._voice_names]
        hindi_candidates = [
            "microsoft heera desktop",
            "microsoft swara desktop",
            "microsoft kalpana desktop",
            "microsoft hemant desktop",
        ]
        english_candidates = [
            "microsoft zira desktop",
            "microsoft david desktop",
            "microsoft hazel desktop",
            "microsoft mark desktop",
        ]

        candidates = hindi_candidates if self.current_language.startswith("hi") else english_candidates
        for candidate in candidates:
            if candidate in available:
                return candidate.title()

        if self._voice_names:
            return self._voice_names[0]

        return "Microsoft Zira Desktop"

    def _get_windows_voice_names(self) -> list[str]:
        script = (
            "Add-Type -AssemblyName System.Speech; "
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            "$s.GetInstalledVoices() | ForEach-Object { $_.VoiceInfo.Name }"
        )

        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    script,
                ],
                capture_output=True,
                text=True,
                check=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            voices = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            if voices:
                print("[speaker] available voices:")
                for voice_name in voices:
                    print(f" - {voice_name}")
            return voices
        except Exception as exc:
            print(f"[speaker_error] get_windows_voices: {exc}")
            return []


if __name__ == "__main__":
    print("[speaker] testing...")
    speaker = Speaker(rate=175, volume=1.0)
    speaker.speak("Hello, this is a test")
    speaker.set_language("hi-IN")
    speaker.speak("Namaste, yeh ek test hai.")
