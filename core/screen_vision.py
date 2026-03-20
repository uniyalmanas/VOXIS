import ollama
import pyautogui
import base64
from io import BytesIO

class ScreenVision:
    def __init__(self):
        self.model = 'llava'
        print("VOXIS Screen Vision - Initialized ✅")

    def capture(self):
        screen = pyautogui.screenshot()
        buffer = BytesIO()
        screen.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode()

    def see(self, question="What do you see on this screen?"):
        try:
            img_data = self.capture()
            response = ollama.chat(
                model=self.model,
                messages=[{
                    'role': 'user',
                    'content': question,
                    'images': [img_data]
                }]
            )
            return response['message']['content']
        except Exception as e:
            print(f"Screen Vision Error: {e}")
            return ""

    def find_element(self, element):
        question = f"""
        Look at this screen carefully.
        Find: {element}
        Reply with ONLY a JSON object:
        {{"found": true/false, "description": "where it is"}}
        """
        return self.see(question)

    def summarize_screen(self):
        return self.see(
            "Summarize what's on this screen in 2 sentences."
        )

if __name__ == "__main__":
    vision = ScreenVision()
    print("Testing screen vision...")
    print(vision.summarize_screen()) 