import speech_recognition as sr
import pyttsx3
import pyautogui
import subprocess
import time

class VoiceEngine:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.speaker = pyttsx3.init()
        self.speaker.setProperty('rate', 175)
        self.speaker.setProperty('volume', 1.0)
        self.wake_word = "jarvis"
        self.commands = {
            "open vs code":     self.open_vscode,
            "open notepad":     self.open_notepad,
            "close window":     self.close_window,
            "take screenshot":  self.take_screenshot,
            "volume up":        self.volume_up,
            "volume down":      self.volume_down,
            "mute":             self.volume_mute,
            "scroll up":        lambda: pyautogui.scroll(5),
            "scroll down":      lambda: pyautogui.scroll(-5),
            "go back":          lambda: pyautogui.hotkey('alt', 'left'),
            "new tab":          lambda: pyautogui.hotkey('ctrl', 't'),
            "close tab":        lambda: pyautogui.hotkey('ctrl', 'w'),
            "switch tab":       lambda: pyautogui.hotkey('ctrl', 'tab'),
            "select all":       lambda: pyautogui.hotkey('ctrl', 'a'),
            "copy":             lambda: pyautogui.hotkey('ctrl', 'c'),
            "paste":            lambda: pyautogui.hotkey('ctrl', 'v'),
            "undo":             lambda: pyautogui.hotkey('ctrl', 'z'),
        }
        print("VOXIS Voice Engine - Initialized")

    def open_vscode(self):
        subprocess.Popen(
            'C:/Users/uniya/AppData/Local/Programs/Microsoft VS Code/Code.exe'
        )

    def open_notepad(self):
        subprocess.Popen('notepad.exe')

    def close_window(self):
        pyautogui.hotkey('alt', 'f4')

    def take_screenshot(self):
        pyautogui.hotkey('win', 'shift', 's')

    def volume_up(self):
        for _ in range(10):
            pyautogui.press('volumeup')
        print("Volume increased")

    def volume_down(self):
        for _ in range(10):
            pyautogui.press('volumedown')
        print("Volume decreased")

    def volume_mute(self):
        pyautogui.press('volumemute')
        print("Muted")

    def speak(self, text):
        print(f"VOXIS: {text}")
        self.speaker.say(text)
        self.speaker.runAndWait()

    def listen(self):
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(
                    source, duration=0.1
                )
                audio = self.recognizer.listen(
                    source,
                    timeout=5,
                    phrase_time_limit=4
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

    def execute_command(self, command):
        for key in self.commands:
            if key in command:
                print(f"Executing: {key}")
                self.speak(f"Sure, {key}")
                self.commands[key]()
                return True
        self.speak("Sorry, I didn't understand that")
        return False

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
                    self.execute_command(command)

            time.sleep(0.1)

if __name__ == "__main__":
    engine = VoiceEngine()
    engine.run()