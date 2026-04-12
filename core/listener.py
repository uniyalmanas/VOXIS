import speech_recognition as sr


class VoiceListener:
    def __init__(self, primary_language: str, fallback_language: str):
        self.primary_language = primary_language
        self.fallback_language = fallback_language
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.35
        self.recognizer.phrase_threshold = 0.2
        self.recognizer.non_speaking_duration = 0.25
        self.microphone = sr.Microphone()

        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.3)

        print("Microphone calibrated")

    def set_languages(self, primary_language: str, fallback_language: str) -> None:
        self.primary_language = primary_language
        self.fallback_language = fallback_language

    def listen(self) -> str:
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(
                    source,
                    timeout=2,
                    phrase_time_limit=4,
                )

            for language in (self.primary_language, self.fallback_language):
                try:
                    text = self.recognizer.recognize_google(audio, language=language).lower()
                    if text:
                        return text
                except Exception:
                    continue

            return ""

        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            print("Speech API unavailable")
            return ""
        except KeyboardInterrupt:
            raise
        except Exception:
            return ""
