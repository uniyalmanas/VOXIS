import os
import sys
import threading
import time
import io
import warnings

# UTF-8 output for Hindi/multilingual support
# Simple UTF-8 fix
import locale
locale.setlocale(locale.LC_ALL, '')

# Suppress all warnings
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['GLOG_minloglevel'] = '3'
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from gesture_engine import GestureEngine
from voice_engine import VoiceEngine

class VOXIS:
    def __init__(self):
        print("""
        ██╗   ██╗ ██████╗ ██╗  ██╗██╗███████╗
        ██║   ██║██╔═══██╗╚██╗██╔╝██║██╔════╝
        ██║   ██║██║   ██║ ╚███╔╝ ██║███████╗
        ╚██╗ ██╔╝██║   ██║ ██╔██╗ ██║╚════██║
         ╚████╔╝ ╚██████╔╝██╔╝ ██╗██║███████║
          ╚═══╝   ╚═════╝ ╚═╝  ╚═╝╚═╝╚══════╝
        Voice & Gesture OS Control — STARTING
        """)
        self.voice_ready = threading.Event()
        self.running = True

    def run_voice(self):
        try:
            voice = VoiceEngine()
            self.voice_ready.set()  # Signal voice is ready
            voice.run()
        except Exception as e:
            print(f"⚠️ Voice engine error: {e}")
            self.voice_ready.set()

    def run_gesture(self):
        try:
            # Wait for voice to be fully ready
            self.voice_ready.wait(timeout=10)
            gesture = GestureEngine()
            gesture.run()
        except Exception as e:
            print(f"⚠️ Gesture engine error: {e}")

    def start(self):
        print("VOXIS — Both engines starting...")
        print("Voice: Say 'Jarvis' to activate")
        print("Gesture: Show palm to activate gestures")
        print("Press Ctrl+C to stop")

        voice_thread = threading.Thread(
            target=self.run_voice,
            daemon=True,
            name="VoiceThread"
        )
        gesture_thread = threading.Thread(
            target=self.run_gesture,
            daemon=True,
            name="GestureThread"
        )

        # Start voice first
        voice_thread.start()
        print("Voice thread started ✅")

        # Wait for voice to signal ready
        # instead of fixed 3 second sleep
        print("Waiting for voice to initialize...")
        self.voice_ready.wait(timeout=15)
        print("Voice initialized ✅")

        # Start gesture
        gesture_thread.start()
        print("Gesture thread started ✅")

        try:
            while True:
                # Check if threads are alive
                if not voice_thread.is_alive():
                    print("⚠️ Voice thread died — restarting...")
                    voice_thread = threading.Thread(
                        target=self.run_voice,
                        daemon=True,
                        name="VoiceThread"
                    )
                    voice_thread.start()

                if not gesture_thread.is_alive():
                    print("⚠️ Gesture thread died — restarting...")
                    gesture_thread = threading.Thread(
                        target=self.run_gesture,
                        daemon=True,
                        name="GestureThread"
                    )
                    gesture_thread.start()

                time.sleep(2)

        except KeyboardInterrupt:
            print("\nVOXIS — Shutting down...")
            sys.exit(0)

if __name__ == "__main__":
    voxis = VOXIS()
    voxis.start()