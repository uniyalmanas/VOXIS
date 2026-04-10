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
import urllib.parse
import importlib.util

# Load settings
sys_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'settings.py')
spec = importlib.util.spec_from_file_location("settings", sys_path)
settings = importlib.util.module_from_spec(spec)
spec.loader.exec_module(settings)

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from ai_brain import AIBrain
from screen_vision import ScreenVision

class VoiceEngine:
    FAST_COMMANDS = {
        # Volume
        "volume up":            lambda self: [pyautogui.press('volumeup') for _ in range(10)],
        "volume down":          lambda self: [pyautogui.press('volumedown') for _ in range(10)],
        "mute":                 lambda self: pyautogui.press('volumemute'),
        "unmute":               lambda self: pyautogui.press('volumemute'),
        # Hindi volume
        "volume badha":         lambda self: [pyautogui.press('volumeup') for _ in range(10)],
        "volume kam karo":      lambda self: [pyautogui.press('volumedown') for _ in range(10)],
        "awaaz badha":          lambda self: [pyautogui.press('volumeup') for _ in range(10)],
        "awaaz kam karo":       lambda self: [pyautogui.press('volumedown') for _ in range(10)],

        # Screenshots
        "screenshot":           lambda self: self._take_screenshot(),
        "take screenshot":      lambda self: self._take_screenshot(),
        "capture screen":       lambda self: self._take_screenshot(),
        "take a photo":         lambda self: subprocess.Popen(['cmd', '/c', 'start', 'microsoft.windows.camera:']),
        "take photo":           lambda self: subprocess.Popen(['cmd', '/c', 'start', 'microsoft.windows.camera:']),
        "click a photo":        lambda self: subprocess.Popen(['cmd', '/c', 'start', 'microsoft.windows.camera:']),

        # Scrolling
        "scroll up":            lambda self: pyautogui.scroll(5),
        "scroll down":          lambda self: pyautogui.scroll(-5),
        "page up":              lambda self: pyautogui.press('pageup'),
        "page down":            lambda self: pyautogui.press('pagedown'),
        "go to top":            lambda self: pyautogui.hotkey('ctrl', 'home'),
        "go to bottom":         lambda self: pyautogui.hotkey('ctrl', 'end'),
        # Hindi scroll
        "upar jao":             lambda self: pyautogui.scroll(5),
        "neeche jao":           lambda self: pyautogui.scroll(-5),

        # Window control
        "close":                lambda self: pyautogui.hotkey('alt', 'f4'),
        "close window":         lambda self: pyautogui.hotkey('alt', 'f4'),
        "minimize":             lambda self: pyautogui.hotkey('win', 'down'),
        "maximize":             lambda self: pyautogui.hotkey('win', 'up'),
        "show desktop":         lambda self: pyautogui.hotkey('win', 'd'),
        "task view":            lambda self: pyautogui.hotkey('win', 'tab'),
        "switch app":           lambda self: pyautogui.hotkey('alt', 'tab'),
        "switch window":        lambda self: pyautogui.hotkey('alt', 'tab'),
        "lock screen":          lambda self: pyautogui.hotkey('win', 'l'),
        # Hindi window
        "band karo":            lambda self: pyautogui.hotkey('alt', 'f4'),
        "chota karo":           lambda self: pyautogui.hotkey('win', 'down'),
        "bada karo":            lambda self: pyautogui.hotkey('win', 'up'),

        # Tabs
        "new tab":              lambda self: pyautogui.hotkey('ctrl', 't'),
        "close tab":            lambda self: pyautogui.hotkey('ctrl', 'w'),
        "next tab":             lambda self: pyautogui.hotkey('ctrl', 'tab'),
        "previous tab":         lambda self: pyautogui.hotkey('ctrl', 'shift', 'tab'),
        "reopen tab":           lambda self: pyautogui.hotkey('ctrl', 'shift', 't'),
        "refresh":              lambda self: pyautogui.hotkey('ctrl', 'r'),
        "reload":               lambda self: pyautogui.hotkey('ctrl', 'r'),
        "go back":              lambda self: pyautogui.hotkey('alt', 'left'),
        "go forward":           lambda self: pyautogui.hotkey('alt', 'right'),

        # Editing
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

        # Apps
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
        # Hindi apps
        "youtube khol":         lambda self: subprocess.Popen(['cmd', '/c', 'start', 'https://www.youtube.com']),
        "youtube kholo":        lambda self: subprocess.Popen(['cmd', '/c', 'start', 'https://www.youtube.com']),
        "google khol":          lambda self: subprocess.Popen(['cmd', '/c', 'start', 'https://www.google.com']),
        "google kholo":         lambda self: subprocess.Popen(['cmd', '/c', 'start', 'https://www.google.com']),
        "gmail khol":           lambda self: subprocess.Popen(['cmd', '/c', 'start', 'https://mail.google.com']),
        "whatsapp khol":        lambda self: subprocess.Popen(['cmd', '/c', 'start', 'https://web.whatsapp.com']),
        "instagram khol":       lambda self: subprocess.Popen(['cmd', '/c', 'start', 'https://www.instagram.com']),
        "calculator khol":      lambda self: subprocess.Popen('calc.exe'),
        "notepad khol":         lambda self: subprocess.Popen('notepad.exe'),

        # Screen vision
        "what's on my screen":  lambda self: self.speak(self._get_vision().summarize_screen()),
        "read my screen":       lambda self: self.speak(self._get_vision().summarize_screen()),
        "what do you see":      lambda self: self.speak(self._get_vision().summarize_screen()),
        "summarize screen":     lambda self: self.speak(self._get_vision().summarize_screen()),
        "screen dekho":         lambda self: self.speak(self._get_vision().summarize_screen()),
        "screen batao":         lambda self: self.speak(self._get_vision().summarize_screen()),

        "switch to hindi":    lambda self: self._set_language("hi-IN", "en-IN", "Hindi"),
        "switch to english":  lambda self: self._set_language("en-IN", "en-US", "English"),
        "hindi mode":         lambda self: self._set_language("hi-IN", "en-IN", "Hindi"),
        "english mode":       lambda self: self._set_language("en-IN", "en-US", "English"),    
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

        self.wake_words = [
          "jarvis", "जारविस",
          "hey jarvis", "हे जारविस",
          "अरे जारविस", "voxis"
        ]
        self.brain = AIBrain()
        self.vision = None

        # Language settings
        self.primary_language = settings.PRIMARY_LANGUAGE
        self.fallback_language = settings.FALLBACK_LANGUAGE

        print(f"Language: {self.primary_language} → {self.fallback_language}")
        print("VOXIS Voice Engine - Initialized")

    def _take_screenshot(self):
        folder = os.path.join(os.path.expanduser("~"), "Pictures")
        os.makedirs(folder, exist_ok=True)
        filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        path = os.path.join(folder, filename)
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

            # Try primary language first
            try:
                text = self.recognizer.recognize_google(
                    audio,
                    language=self.primary_language
                ).lower()
                if text:
                    return text
            except Exception:
                pass

            # Try fallback language
            try:
                text = self.recognizer.recognize_google(
                    audio,
                    language=self.fallback_language
                ).lower()
                if text:
                    return text
            except Exception:
                pass

            return ""

        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            print("⚠️ Speech API unavailable")
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
            elif "whatsapp" in app:
                subprocess.Popen(['cmd', '/c', 'start', 'https://web.whatsapp.com'])
                self.speak("Opening WhatsApp")
            elif "instagram" in app:
                subprocess.Popen(['cmd', '/c', 'start', 'https://www.instagram.com'])
                self.speak("Opening Instagram")
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
            query_encoded = urllib.parse.quote(query)
            if "youtube" in platform or "youtube" in query:
                query_clean = query.replace("youtube", "").strip()
                query_encoded = urllib.parse.quote(query_clean)
                url = f'https://www.youtube.com/results?search_query={query_encoded}'
            else:
                url = f'https://www.google.com/search?q={query_encoded}'
            subprocess.Popen(['cmd', '/c', 'start', '', url])
            self.speak(f"Searching for {query}")

        elif action == "unknown":
            self.speak("Sorry, I didn't understand that")

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

            # Remove mode labels
            if "MODE 1" in response_clean or "MODE 2" in response_clean:
                json_match = re.search(r'\{.*\}', response_clean, re.DOTALL)
                if json_match:
                    response_clean = json_match.group()
                else:
                    self.speak(response_clean)
                    return

            # Handle mixed text + JSON
            if '{' in response_clean and '"action"' in response_clean:
                json_match = re.search(r'\{.*\}', response_clean, re.DOTALL)
                if json_match:
                    text_before = response_clean[:response_clean.index('{')].strip()
                    if text_before:
                        self.speak(text_before)
                    json_str = json_match.group()
                    data = json.loads(json_str)
                    action = data.get("action", "unknown")
                    params = data.get("params", {})
                    print(f"Action: {action} | Params: {params}")
                    self.execute_action(action, params)
                    return

            # Remove markdown
            if "```" in response_clean:
                response_clean = response_clean.split("```")[1]
                if response_clean.startswith("json"):
                    response_clean = response_clean[4:]

            # Pure JSON
            if response_clean.startswith('{'):
                data = json.loads(response_clean)
                action = data.get("action", "unknown")
                params = data.get("params", {})
                print(f"Action: {action} | Params: {params}")
                self.execute_action(action, params)
            else:
                print(f"VOXIS says: {response_clean}")
                self.speak(response_clean)

        except json.JSONDecodeError:
            print(f"VOXIS says: {response}")
            self.speak(response)

    def run(self):
        self.speak("VOXIS is ready")
        print("Say 'Jarvis' to activate")
        print(f"Languages: {self.primary_language} + {self.fallback_language}")
        while True:
            print("Listening...")
            audio = self.listen()
            if audio:
                print(f"Heard: '{audio}'")
            wake_words = [
                "jarvis",
                "जारविस",
                "hey jarvis",
                "हे जारविस",
                "अरे जारविस",
                "voxis",
                "वॉक्सिस",
            ]
            
            if any(word in audio for word in wake_words):
                self.speak("Yes?")
                print("Listening for command...")
                command = self.listen()
                if command:
                    print(f"Command: {command}")
                    self.process_command(command)
            time.sleep(0.1)
            
            
    def _set_language(self, primary, fallback, name):
        self.primary_language = primary
        self.fallback_language = fallback
        self.speak(f"Switched to {name} mode")
        print(f"Language: {primary} ✅")
if __name__ == "__main__":
    engine = VoiceEngine()
    engine.run()