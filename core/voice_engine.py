import speech_recognition as sr
import pyttsx3
import pyautogui
import subprocess
import time
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from ai_brain import AIBrain

class VoiceEngine:
    # Layer 1 — Fast commands, bypass AI completely
    FAST_COMMANDS = {
        "volume up":    lambda: [pyautogui.press('volumeup') for _ in range(10)],
        "volume down":  lambda: [pyautogui.press('volumedown') for _ in range(10)],
        "mute":         lambda: pyautogui.press('volumemute'),
        "screenshot":   lambda: pyautogui.hotkey('win', 'shift', 's'),
        "scroll up":    lambda: pyautogui.scroll(5),
        "scroll down":  lambda: pyautogui.scroll(-5),
        "close":        lambda: pyautogui.hotkey('alt', 'f4'),
        "new tab":      lambda: pyautogui.hotkey('ctrl', 't'),
        "close tab":    lambda: pyautogui.hotkey('ctrl', 'w'),
        "go back":      lambda: pyautogui.hotkey('alt', 'left'),
        "copy":         lambda: pyautogui.hotkey('ctrl', 'c'),
        "paste":        lambda: pyautogui.hotkey('ctrl', 'v'),
        "select all":   lambda: pyautogui.hotkey('ctrl', 'a'),
        "undo":         lambda: pyautogui.hotkey('ctrl', 'z'),
    }

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = False
        self.recognizer.pause_threshold = 0.5
        self.microphone = sr.Microphone()

        # Calibrate microphone once at startup
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Microphone calibrated ✅")

        self.speaker = pyttsx3.init()
        self.speaker.setProperty('rate', 175)
        self.speaker.setProperty('volume', 1.0)
        self.wake_word = "jarvis"

        # Initialize AI Brain
        self.brain = AIBrain()

        print("VOXIS Voice Engine - Initialized")

    def speak(self, text):
        print(f"VOXIS: {text}")
        self.speaker.say(text)
        self.speaker.runAndWait()

    def listen(self):
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(
                    source,
                    timeout=3,
                    phrase_time_limit=3
                )
            text = self.recognizer.recognize_google(
                audio,
                language="en-IN"
            ).lower()
            return text
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            print(f"API Error: {e}")
            return ""
        except KeyboardInterrupt:
            raise
        except Exception:
            return ""

    def execute_action(self, action, params):
        if action == "open_app":
            app = params.get("app_name", "").lower()
            if "youtube" in app:
                subprocess.Popen(['cmd', '/c', 'start', 'https://www.youtube.com'])
                self.speak("Opening YouTube")
            elif "linkedin" in app:
                subprocess.Popen(['cmd', '/c', 'start', 'https://www.linkedin.com'])
                self.speak("Opening LinkedIn")
            elif "google" in app:
                subprocess.Popen(['cmd', '/c', 'start', 'https://www.google.com'])
                self.speak("Opening Google")
            elif "vs code" in app or "vscode" in app or "code" in app:
                subprocess.Popen(
                    'C:/Users/uniya/AppData/Local/Programs/Microsoft VS Code/Code.exe'
                )
                self.speak("Opening VS Code")
            elif "notepad" in app:
                subprocess.Popen('notepad.exe')
                self.speak("Opening Notepad")
            elif "chrome" in app:
                subprocess.Popen(['cmd', '/c', 'start', 'chrome'])
                self.speak("Opening Chrome")
            elif "spotify" in app:
                subprocess.Popen(['cmd', '/c', 'start', 'spotify'])
                self.speak("Opening Spotify")
            else:
                subprocess.Popen(['cmd', '/c', 'start', app])
                self.speak(f"Opening {app}")

        elif action == "volume_up":
            for _ in range(10):
                pyautogui.press('volumeup')
            self.speak("Volume up")

        elif action == "volume_down":
            for _ in range(10):
                pyautogui.press('volumedown')
            self.speak("Volume down")

        elif action == "mute":
            pyautogui.press('volumemute')
            self.speak("Muted")

        elif action == "scroll_up":
            pyautogui.scroll(5)

        elif action == "scroll_down":
            pyautogui.scroll(-5)

        elif action == "close_window":
            pyautogui.hotkey('alt', 'f4')
            self.speak("Closing window")

        elif action == "take_screenshot":
            pyautogui.hotkey('win', 'shift', 's')
            self.speak("Screenshot taken")

        elif action == "new_tab":
            pyautogui.hotkey('ctrl', 't')

        elif action == "close_tab":
            pyautogui.hotkey('ctrl', 'w')

        elif action == "search":
            query = params.get("query", "")
            subprocess.Popen([
                'cmd', '/c', 'start',
                f'https://google.com/search?q={query}'
            ])
            self.speak(f"Searching for {query}")

        elif action == "unknown":
            self.speak("Sorry, I didn't understand that")

    def process_command(self, command):
        # Layer 1 — check fast commands first
        for key in self.FAST_COMMANDS:
            if key in command:
                print(f"Fast executing: {key} ⚡")
                self.FAST_COMMANDS[key]()
                return

        # Layer 2 — unknown command, use AI
        print(f"Thinking... 🧠")
        response = self.brain.think(command)
        try:
            response = response.strip()
            if "```" in response:
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            data = json.loads(response)
            action = data.get("action", "unknown")
            params = data.get("params", {})
            print(f"Action: {action} | Params: {params}")
            self.execute_action(action, params)
        except json.JSONDecodeError:
            print(f"Could not parse: {response}")
            self.speak("Sorry, something went wrong")

    def run(self):
        self.speak("VOXIS is ready")
        print("Say 'Jarvis' to activate")

        while True:
            print("Listening...")
            audio = self.listen()

            if audio:
                print(f"Heard: '{audio}'")

            if self.wake_word in audio:
                self.speak("Yes?")
                print("Listening for command...")
                command = self.listen()
                if command:
                    print(f"Command: {command}")
                    self.process_command(command)

            time.sleep(0.1)

if __name__ == "__main__":
    engine = VoiceEngine()
    engine.run()