import locale
import os
import sys
import threading
import warnings

locale.setlocale(locale.LC_ALL, "")

warnings.filterwarnings("ignore")
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["GLOG_minloglevel"] = "3"
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "core"))

from gesture_engine import GestureEngine
from voice_runtime import VoiceEngine


class VOXIS:
    def __init__(self):
        print(
            """
        VOXIS
        Voice & Gesture OS Control - STARTING
        """
        )
        self.voice_ready = threading.Event()
        self.voice = None

    def run_gesture(self):
        try:
            self.voice_ready.wait(timeout=10)
            gesture = GestureEngine()
            gesture.run()
        except Exception as exc:
            print(f"[main_error] gesture engine: {exc}")

    def start(self):
        print("VOXIS - Both engines starting...")
        print("Voice: Say 'Jarvis' to activate")
        print("Gesture: Show palm to activate gestures")
        print("Press Ctrl+C to stop")

        gesture_thread = threading.Thread(
            target=self.run_gesture,
            daemon=True,
            name="GestureThread",
        )

        try:
            print("Initializing voice runtime on main thread...")
            self.voice = VoiceEngine()
            self.voice_ready.set()
            print("Voice runtime initialized")

            gesture_thread.start()
            print("Gesture thread started")

            self.voice.run()
        except KeyboardInterrupt:
            print("\nVOXIS - Shutting down...")
            sys.exit(0)
        except Exception as exc:
            self.voice_ready.set()
            print(f"[main_error] voice engine: {exc}")
            sys.exit(1)


if __name__ == "__main__":
    voxis = VOXIS()
    voxis.start()
