import speech_recognition as sr
import pyttsx3
import pyautogui
import subprocess
import time
import json
import sys
import os
import datetime
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from ai_brain import AIBrain
from screen_vision import ScreenVision

class VoiceEngine:
    FAST_COMMANDS = {
        "volume up":            lambda self: [pyautogui.press('volumeup') for _ in range(10)],
        "volume down":          lambda self: [pyautogui.press('volumedown') for _ in range(10)],
        "mute":                 lambda self: pyautogui.press('volumemute'),
        "unmute":               lambda self: pyautogui.press('volumemute'),
        "screenshot":           lambda self: self._take_screenshot(),
        "take screenshot":      lambda self: self._take_screenshot(),
        "capture screen":       lambda self: self._take_screenshot(),
        "take a photo":         lambda self: subprocess.Popen(['cmd', '/c', 'start', 'microsoft.windows.camera:']),
        "take photo":           lambda self: subprocess.Popen(['cmd', '/c', 'start', 'microsoft.windows.camera:']),
        "click a photo":        lambda self: subprocess.Popen(['cmd', '/c', 'start', 'microsoft.windows.camera:']),
        "scroll up":            lambda self: pyautogui.scroll(5),
        "scroll down":          lambda self: pyautogui.scroll(-5),
        "page up":              lambda self: pyautogui.press('pageup'),
        "page down":            lambda self: pyautogui.press('pagedown'),
        "go to top":            lambda self: pyautogui.hotkey('ctrl', 'home'),
        "go to bottom":         lambda self: pyautogui.hotkey('ctrl', 'end'),
        "close":                lambda self: pyautogui.hotkey('alt', 'f4'),
        "close window":         lambda self: pyautogui.hotkey('alt', 'f4'),
        "minimize":             lambda self: pyautogui.hotkey('win', 'down'),
        "maximize":             lambda self: pyautogui.hotkey('win', 'up'),
        "new tab":              lambda self: pyautogui.hotkey('ctrl', 't'),
        "close tab":            lambda self: pyautogui.hotkey('ctrl', 'w'),
        "next tab":             lambda self: pyautogui.hotkey('ctrl', 'tab'),
        "previous tab":         lambda self: pyautogui.hotkey('ctrl', 'shift', 'tab'),
        "reopen tab":           lambda self: pyautogui.hotkey('ctrl', 'shift', 't'),
        "refresh":              lambda self: pyautogui.hotkey('ctrl', 'r'),
        "reload":               lambda self: pyautogui.hotkey('ctrl', 'r'),
        "go back":              lambda self: pyautogui.hotkey('alt', 'left'),
        "go forward":           lambda self: pyautogui.hotkey('alt', 'right'),
        "copy":                 lambda self: pyautogui.hotkey('ctrl', 'c'),
        "paste":                lambda self: pyautogui.hotkey('ctrl', 'v'),
        "cut":                  lambda self: pyautogui.hotkey('ctrl', 'x'),
        "select all":           lambda self: pyautogui.hotkey('ctrl', 'a'),
        "undo":                 lambda self: pyautogui.hotkey('ctrl', 'z'),
        "redo":                 lambda self: pyautogui.hotkey('ctrl', 'y'),
        "save":                 lambda self: pyautogui.hotkey('ctrl', 's'),
        "find":                 lambda self: pyautogui.hotkey('ctrl', 'f'),
        "zoom in":              lambda self: pyautogui.hotkey('ctrl', '+'),
        "zoom out":             lambda self: pyautogui.hotkey('ctrl', '-'),
        "open youtube":         lambda self: subprocess.Popen(['cmd', '/c', 'start', 'https://www.youtube.com']),
        "open linkedin":        lambda self: subprocess.Popen(['cmd', '/c', 'start', 'https://www.linkedin.com']),
        "open gmail":           lambda self: subprocess.Popen(['cmd', '/c', 'start', 'https://mail.google.com']),
        "open google":          lambda self: subprocess.Popen(['cmd', '/c', 'start', 'https://www.google.com']),
        "open github":          lambda self: subprocess.Popen(['cmd', '/c', 'start', 'https://www.github.com']),
        "open twitter":         lambda self: subprocess.Popen(['cmd', '/c', 'start', 'https://www.twitter.com']),
        "open whatsapp":        lambda self: subprocess.Popen(['cmd', '/c', 'start', 'https://web.whatsapp.com']),
        "open instagram":       lambda self: subprocess.Popen(['cmd', '/c', 'start', 'https://www.instagram.com']),
        "open netflix":         lambda self: subprocess.Popen(['cmd', '/c', 'start', 'https://www.netflix.com']),
        "open spotify":         lambda self: subprocess.Popen(['cmd', '/c', 'start', 'spotify:']),
        "open notepad":         lambda self: subprocess.Popen('notepad.exe'),
        "open calculator":      lambda self: subprocess.Popen('calc.exe'),
        "open camera":          lambda self: subprocess.Popen(['cmd', '/c', 'start', 'microsoft.windows.camera:']),
        "open settings":        lambda self: subprocess.Popen(['cmd', '/c', 'start', 'ms-settings:']),
        "open vs code":         lambda self: subprocess.Popen('C:/Users/uniya/AppData/Local/Programs/Microsoft VS Code/Code.exe'),
        "open code":            lambda self: subprocess.Popen('C:/Users/uniya/AppData/Local/Programs/Microsoft VS Code/Code.exe'),
        "open file explorer":   lambda self: subprocess.Popen('explorer.exe'),
        "open task manager":    lambda self: subprocess.Popen('taskmgr.exe'),
        "lock screen":          lambda self: pyautogui.hotkey('win', 'l'),
        "show desktop":         lambda self: pyautogui.hotkey('win', 'd'),
        "task view":            lambda self: pyautogui.hotkey('win', 'tab'),
        "switch app":           lambda self: pyautogui.hotkey('alt', 'tab'),
        "switch window":        lambda self: pyautogui.hotkey('alt', 'tab'),
        "what's on my screen":  lambda self: self.speak(self._get_vision().summarize_screen()),
        "read my screen":       lambda self: self.speak(self._get_vision().summarize_screen()),
        "what do you see":      lambda self: self.speak(self._get_vision().summarize_screen()),
        "summarize screen":     lambda self: self.speak(self._get_vision().summarize_screen()),
    }

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = False
        self.recognizer.pause_threshold = 0.5
        self.microphone = sr.Microphone()
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Microphone calibrated ✅")
        self.speaker = pyttsx3.init()
        self.speaker.setProperty('rate', 175)
        self.speaker.setProperty('volume', 1.0)
        self.wake_word = "jarvis"
        self.brain = AIBrain()
        self.vision = None
        print("VOXIS Voice Engine - Initialized")

    def _take_screenshot(self):
        filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        path = os.path.join(os.path.expanduser("~"), "Pictures", filename)
        pyautogui.screenshot(path)
        self.speak("Screenshot saved")
        print(f"Saved to: {path}")

    def _get_vision(self):
        if self.vision is None:
            print("Loading screen vision... 👁️")
            self.vision = ScreenVision()
        return self.vision

    def speak(self, text):
        print(f"VOXIS: {text}")
        self.speaker.say(text)
        self.speaker.runAndWait()

    def listen(self):
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(
                    source,
                    timeout=5,
                    phrase_time_limit=5
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
            elif "gmail" in app or "mail" in app:
                subprocess.Popen(['cmd', '/c', 'start', 'https://mail.google.com'])
                self.speak("Opening Gmail")
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
                subprocess.Popen(['cmd', '/c', 'start', 'spotify:'])
                self.speak("Opening Spotify")
            elif "camera" in app:
                subprocess.Popen(['cmd', '/c', 'start', 'microsoft.windows.camera:'])
                self.speak("Opening camera")
            elif "calculator" in app:
                subprocess.Popen('calc.exe')
                self.speak("Opening calculator")
            elif "settings" in app:
                subprocess.Popen(['cmd', '/c', 'start', 'ms-settings:'])
                self.speak("Opening settings")
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
            self._take_screenshot()

        elif action == "new_tab":
            pyautogui.hotkey('ctrl', 't')

        elif action == "close_tab":
            pyautogui.hotkey('ctrl', 'w')

        elif action == "search":
             query = params.get("query", "")
             platform = params.get("platform", "google")
             
             # URL encode the query
             import urllib.parse
             query_encoded = urllib.parse.quote(query)
             
             if "youtube" in platform or "youtube" in query:
                 query_clean = query.replace("youtube", "").strip()
                 query_encoded = urllib.parse.quote(query_clean)
                 url = f'https://www.youtube.com/results?search_query={query_encoded}'
             else:
                 url = f'https://www.google.com/search?q={query_encoded}'
             
             subprocess.Popen(['cmd', '/c', 'start', '', url])
             self.speak(f"Searching for {query}")
         
        

    def process_command(self, command):
        # Layer 1 — fast commands
        for key in self.FAST_COMMANDS:
            if key in command:
                print(f"Fast executing: {key} ⚡")
                self.FAST_COMMANDS[key](self)
                return

        # Layer 2 — AI brain
        print(f"Thinking... 🧠")
        response = self.brain.think(command)

        try:
            response_clean = response.strip()

            # Remove mode labels if LLM adds them
            if "MODE 1" in response_clean or "MODE 2" in response_clean:
                json_match = re.search(r'\{.*\}', response_clean, re.DOTALL)
                if json_match:
                    response_clean = json_match.group()
                else:
                    self.speak(response_clean)
                    return

            # Remove markdown code blocks
            if "```" in response_clean:
                response_clean = response_clean.split("```")[1]
                if response_clean.startswith("json"):
                    response_clean = response_clean[4:]

            # Try JSON first
            if response_clean.startswith('{'):
                data = json.loads(response_clean)
                action = data.get("action", "unknown")
                params = data.get("params", {})
                print(f"Action: {action} | Params: {params}")
                self.execute_action(action, params)
            else:
                # Chat response
                print(f"VOXIS says: {response_clean}")
                self.speak(response_clean)

        except json.JSONDecodeError:
            print(f"VOXIS says: {response}")
            self.speak(response)

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