import speech_recognition as sr


class VoiceListener:
    def __init__(self, primary_language: str, fallback_language: str):
        self.primary_language = primary_language
        self.fallback_language = fallback_language

        self.recognizer = sr.Recognizer()

        # 🔥 FIXED SETTINGS
        self.recognizer.energy_threshold = 250
        self.recognizer.dynamic_energy_threshold = True

        # IMPORTANT: increase these
        self.recognizer.pause_threshold = 1.0
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 0.5

        self.microphone = sr.Microphone()

        # 🔥 Better calibration
        with self.microphone as source:
            print("🎤 Calibrating microphone...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print(f"🎤 Energy threshold: {self.recognizer.energy_threshold}")

        print("✅ Microphone calibrated")

    def set_languages(self, primary_language: str, fallback_language: str) -> None:
        self.primary_language = primary_language
        self.fallback_language = fallback_language

    def listen(self) -> str:
        try:
            with self.microphone as source:
                print("🎤 Listening...")

                audio = self.recognizer.listen(
                    source,
                    timeout=5,              # increased
                    phrase_time_limit=5     # increased
                )

            for language in (self.primary_language, self.fallback_language):
                try:
                    text = self.recognizer.recognize_google(audio, language=language).lower()
                    if text:
                        print(f"🎤 Recognized ({language}): {text}")
                        return text
                except Exception:
                    continue

            return ""

        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            print("❌ Speech API unavailable")
            return ""
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"❌ Listener error: {e}")
            return ""