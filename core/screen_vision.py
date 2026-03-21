import ollama
import pyautogui
import base64
import os
import sys
from io import BytesIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import importlib.util
spec = importlib.util.spec_from_file_location(
    "settings",
    os.path.join(os.path.dirname(__file__), '..', 'config', 'settings.py')
)
settings = importlib.util.module_from_spec(spec)
spec.loader.exec_module(settings)

class ScreenVision:
    def __init__(self):
        self.use_gemini = True
        try:
            from google import genai
            from google.genai import types
            self.genai = genai
            self.types = types
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            self.gemini_model = settings.GEMINI_MODEL
            print("VOXIS Screen Vision - Initialized ✅ (Gemini)")
        except Exception:
            self.use_gemini = False
            self.local_model = 'llava'
            print("VOXIS Screen Vision - Initialized ✅ (Local LLaVA)")

    def capture(self):
        """Take screenshot — returns bytes"""
        img = pyautogui.screenshot()
        buf = BytesIO()
        img.save(buf, format='PNG')
        return buf.getvalue()

    def capture_base64(self):
        """Take screenshot — returns base64"""
        return base64.b64encode(self.capture()).decode()

    def see(self, question="What do you see on this screen?"):
        """See screen — uses Gemini if available else LLaVA"""
        if self.use_gemini:
            return self._see_gemini(question)
        return self._see_local(question)

    def _see_gemini(self, question):
        """Fast vision via Gemini"""
        try:
            img_bytes = self.capture()
            response = self.client.models.generate_content(
                model=self.gemini_model,
                contents=[
                    self.types.Part.from_bytes(
                        data=img_bytes,
                        mime_type="image/png"
                    ),
                    question
                ]
            )
            return response.text.strip()
        except Exception as e:
            print(f"⚠️ Gemini vision unavailable → Local")
            self.use_gemini = False
            return self._see_local(question)

    def _see_local(self, question):
        """Private vision via local LLaVA"""
        try:
            img_data = self.capture_base64()
            response = ollama.chat(
                model='llava',
                messages=[{
                    'role': 'user',
                    'content': question,
                    'images': [img_data]
                }]
            )
            return response['message']['content']
        except Exception as e:
            print(f"⚠️ Vision unavailable")
            return "I cannot see the screen right now."

    def summarize_screen(self):
        """2 sentence screen summary"""
        return self.see(
            "Describe what's on this screen in exactly "
            "  2 short sentences. Be specific."
        )

    def find_element(self, element):
        """Find UI element location"""
        return self.see(
            f"Where is the {element} on this screen? "
            f"Describe its location in one sentence."
        )
          
    def read_text(self): 
        """Read all text visible on screen"""
        return self.see(
            "Read and list all visible text on this screen."
        ) 

    def whats_open(self):
        """List all open apps/windows"""
        return self.see(
            "List all open applications and windows "
            "vi sible on this screen."
        )

if __name__ == "__main__":
    vision = ScreenVision()
    print("\nTesting screen vision...")
    print(vision.summarize_screen()) 