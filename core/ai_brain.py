import ollama

class AIBrain:
    def __init__(self):
        self.model = 'llama3'
        self.system_prompt = """
You are VOXIS — an AI assistant that controls 
a computer using voice and gestures.

When user gives you a command, respond with 
a JSON object only. No extra text.

Format:
{
    "action": "command_name",
    "params": {}
}

Available actions:
- open_app (params: app_name)
- volume_up
- volume_down
- mute
- scroll_up
- scroll_down
- close_window
- take_screenshot
- new_tab
- close_tab
- search (params: query)
- unknown (when command is unclear)
        """
        print("VOXIS AI Brain - Initialized ✅")

    def think(self, command):
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        'role': 'system',
                        'content': self.system_prompt
                    },
                    {
                        'role': 'user',
                        'content': command
                    }
                ]
            )
            return response['message']['content']
        except Exception as e:
            print(f"AI Brain Error: {e}")
            return '{"action": "unknown", "params": {}}'

if __name__ == "__main__":
    brain = AIBrain()
    
    # Test commands
    tests = [
        "open youtube",
        "turn down the volume",
        "take a screenshot",
        "open vs code"
    ]
    
    for test in tests:
        print(f"\nCommand: {test}")
        response = brain.think(test)
        print(f"AI Response: {response}")