import threading
import sys
import os
import time

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

    def run_voice(self):
        voice = VoiceEngine()
        voice.run()

    def run_gesture(self):
        gesture = GestureEngine()
        gesture.run()

    def start(self):
        print("VOXIS — Both engines starting...")
        print("Voice: Say 'Jarvis' to activate")
        print("Gesture: Point finger to move cursor")
        print("Press Ctrl+C to stop")

        voice_thread = threading.Thread(
            target=self.run_voice,
            daemon=True
        )
        gesture_thread = threading.Thread(
            target=self.run_gesture,
            daemon=True
        )

        # Start voice first
        voice_thread.start()
        print("Voice thread started ✅")

        # Give voice 3 seconds to initialize
        time.sleep(3)

        # Then start gesture
        gesture_thread.start()
        print("Gesture thread started ✅")

        try:
            while True:
                voice_thread.join(timeout=1)
                gesture_thread.join(timeout=1)
        except KeyboardInterrupt:
            print("\nVOXIS — Shutting down...")
            sys.exit(0)

if __name__ == "__main__":
    voxis = VOXIS()
    voxis.start()