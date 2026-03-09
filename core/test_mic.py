import speech_recognition as sr

# List all microphones
print("Available microphones:")
for index, name in enumerate(sr.Microphone.list_microphone_names()):
    print(f"{index}: {name}")

# Test microphone
r = sr.Recognizer()
print("\nSay something...")
with sr.Microphone() as source:
    r.adjust_for_ambient_noise(source, duration=1)
    audio = r.listen(source, timeout=5)
    
try:
    text = r.recognize_google(audio)
    print(f"You said: {text}")
except Exception as e:
    print(f"Error: {e}")