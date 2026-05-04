import argparse

import speech_recognition as sr


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test microphone capture and speech recognition.")
    parser.add_argument("--device", type=int, default=None, help="Microphone device index.")
    parser.add_argument("--language", default="en-IN", help="Primary recognition language.")
    parser.add_argument("--fallback", default="en-US", help="Fallback recognition language.")
    parser.add_argument("--timeout", type=float, default=5.0, help="Seconds to wait for speech.")
    parser.add_argument("--phrase-limit", type=float, default=6.0, help="Maximum command length in seconds.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print("Available microphones:")
    for index, name in enumerate(sr.Microphone.list_microphone_names()):
        marker = " <- selected" if args.device == index else ""
        print(f"{index}: {name}{marker}")

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 250
    recognizer.dynamic_energy_threshold = True
    recognizer.dynamic_energy_adjustment_damping = 0.15
    recognizer.dynamic_energy_ratio = 1.5
    recognizer.pause_threshold = 0.8
    recognizer.phrase_threshold = 0.3
    recognizer.non_speaking_duration = 0.35

    microphone = sr.Microphone(device_index=args.device)

    with microphone as source:
        print("\nCalibrating room noise...")
        recognizer.adjust_for_ambient_noise(source, duration=0.8)
        print(f"Energy threshold: {recognizer.energy_threshold}")
        print("Say a short command now.")
        audio = recognizer.listen(
            source,
            timeout=args.timeout,
            phrase_time_limit=args.phrase_limit,
        )

    for language in (args.language, args.fallback):
        try:
            text = recognizer.recognize_google(audio, language=language)
            print(f"Recognized ({language}): {text}")
            return
        except sr.UnknownValueError:
            print(f"Could not understand speech with {language}")
        except sr.RequestError as exc:
            print(f"Speech API unavailable for {language}: {exc}")
            return

    print("Audio was captured, but speech was not recognized.")


if __name__ == "__main__":
    main()
