import importlib.util
import json
import os

import speech_recognition as sr

sys_path = os.path.join(os.path.dirname(__file__), "..", "config", "settings.py")
spec = importlib.util.spec_from_file_location("settings", sys_path)
settings = importlib.util.module_from_spec(spec)
spec.loader.exec_module(settings)


class VoiceListener:
    def __init__(self, primary_language: str, fallback_language: str):
        self.primary_language = primary_language
        self.fallback_language = fallback_language
        self.stt_backend = getattr(settings, "STT_BACKEND", "auto").strip().lower()
        self.vosk_model_path = getattr(settings, "VOSK_MODEL_PATH", "").strip()
        self.vosk_model_paths = getattr(settings, "VOSK_MODEL_PATHS", {})
        self._vosk_models = {}
        self._vosk_available = False
        self._google_available = True

        self.recognizer = sr.Recognizer()

        # Tuned recognition settings.
        self.recognizer.energy_threshold = 250
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.15
        self.recognizer.dynamic_energy_ratio = 1.5

        self.listen_timeout = 4
        self.phrase_time_limit = 6
        self._silent_timeouts = 0

        self.recognizer.pause_threshold = 0.8
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 0.35

        self.microphone = sr.Microphone()

        self._init_vosk()
        self.calibrate()

    def calibrate(self, duration: float = 0.8) -> None:
        """Calibrate against room noise without making startup feel sluggish."""
        with self.microphone as source:
            print("Calibrating microphone...")
            self.recognizer.adjust_for_ambient_noise(source, duration=duration)
            print(f"Energy threshold: {self.recognizer.energy_threshold}")

        print("Microphone calibrated")

    def set_languages(self, primary_language: str, fallback_language: str) -> None:
        self.primary_language = primary_language
        self.fallback_language = fallback_language

    def listen(self, timeout: float | None = None, phrase_time_limit: float | None = None) -> str:
        try:
            listen_timeout = timeout if timeout is not None else self.listen_timeout
            phrase_limit = phrase_time_limit if phrase_time_limit is not None else self.phrase_time_limit

            with self.microphone as source:
                print("Listening...")

                audio = self.recognizer.listen(
                    source,
                    timeout=listen_timeout,
                    phrase_time_limit=phrase_limit,
                )

            self._silent_timeouts = 0

            if self.stt_backend in {"auto", "vosk", "local"}:
                text = self._recognize_vosk(audio)
                if text:
                    return text
                if self.stt_backend in {"vosk", "local"}:
                    print("No clear local speech recognized")
                    return ""

            if self.stt_backend in {"auto", "google"} and self._google_available:
                return self._recognize_google(audio)

            print("No speech recognition backend is available")
            return ""

        except sr.WaitTimeoutError:
            self._silent_timeouts += 1
            if self._silent_timeouts % 3 == 0:
                print("Still listening; no speech detected yet")
            return ""
        except sr.UnknownValueError:
            print("No clear speech recognized")
            return ""
        except sr.RequestError as e:
            print(f"Speech API unavailable: {e}")
            return ""
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"Listener error: {e}")
            return ""

    def _recognize_google(self, audio: sr.AudioData) -> str:
        try:
            for language in (self.primary_language, self.fallback_language):
                try:
                    text = self.recognizer.recognize_google(audio, language=language).lower()
                    if text:
                        print(f"Recognized ({language}): {text}")
                        return text
                except sr.UnknownValueError:
                    continue
                except sr.RequestError as e:
                    print(f"Speech API unavailable: {e}")
                    self._google_available = False
                    return ""

            print("No clear speech recognized")
            return ""
        except sr.UnknownValueError:
            print("No clear speech recognized")
            return ""
        except sr.RequestError as e:
            print(f"Speech API unavailable: {e}")
            self._google_available = False
            return ""
        except Exception as e:
            print(f"Google speech recognition error: {e}")
            return ""

    def _init_vosk(self) -> None:
        try:
            from vosk import Model, SetLogLevel
        except Exception:
            if self.stt_backend in {"vosk", "local"}:
                print("Vosk is not installed. Install it with: pip install vosk")
            return

        SetLogLevel(-1)
        model_paths = self._resolve_vosk_model_paths()
        if not model_paths:
            if self.stt_backend in {"vosk", "local"}:
                print("No Vosk model found. Set VOSK_MODEL_PATHS in config/settings.py")
            return

        for language, model_path in model_paths.items():
            try:
                self._vosk_models[language] = Model(model_path)
                self._vosk_available = True
                print(f"Local speech recognition ready ({language}): {model_path}")
            except Exception as e:
                print(f"Could not load Vosk model for {language}: {e}")

    def _resolve_vosk_model_paths(self) -> dict[str, str]:
        resolved = {}
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

        configured_paths = dict(self.vosk_model_paths or {})
        if self.vosk_model_path:
            configured_paths.setdefault("en", self.vosk_model_path)

        for language, configured_path in configured_paths.items():
            normalized = self._normalize_model_path(configured_path, repo_root)
            if os.path.isdir(normalized):
                resolved[self._language_prefix(language)] = normalized

        models_dir = os.path.join(repo_root, "models")
        if os.path.isdir(models_dir):
            for name in os.listdir(models_dir):
                path = os.path.join(models_dir, name)
                if not os.path.isdir(path) or not name.lower().startswith("vosk-model"):
                    continue

                if "-hi-" in name.lower():
                    resolved.setdefault("hi", path)
                elif "-en-" in name.lower():
                    resolved.setdefault("en", path)

        return resolved

    def _normalize_model_path(self, path: str, repo_root: str) -> str:
        expanded = os.path.expanduser(str(path))
        if os.path.isabs(expanded):
            return os.path.abspath(expanded)
        return os.path.abspath(os.path.join(repo_root, expanded))

    def _recognize_vosk(self, audio: sr.AudioData) -> str:
        if not self._vosk_available or not self._vosk_models:
            return ""

        try:
            from vosk import KaldiRecognizer

            raw_audio = audio.get_raw_data(convert_rate=16000, convert_width=2)
            for language in self._vosk_language_order():
                model = self._vosk_models.get(language)
                if model is None:
                    continue

                recognizer = KaldiRecognizer(model, 16000)
                recognizer.SetWords(False)
                recognizer.AcceptWaveform(raw_audio)
                result = json.loads(recognizer.FinalResult())
                text = result.get("text", "").strip().lower()
                if text:
                    print(f"Recognized (local {language}): {text}")
                    return text

            return ""
        except Exception as e:
            print(f"Local speech recognition error: {e}")
            return ""

    def _vosk_language_order(self) -> list[str]:
        languages = [
            self._language_prefix(self.primary_language),
            self._language_prefix(self.fallback_language),
            "en",
            "hi",
        ]
        ordered = []
        for language in languages:
            if language in self._vosk_models and language not in ordered:
                ordered.append(language)
        return ordered

    def _language_prefix(self, language: str) -> str:
        return str(language or "").split("-", 1)[0].strip().lower()
