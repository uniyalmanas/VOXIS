# VOXIS

## Real-Time Voice and Gesture Desktop Copilot

VOXIS is a local-first desktop assistant that lets you control your computer through voice and hand gestures. It is being built as a real-time AI collaborator: you speak, VOXIS understands the intent, takes action on your system, talks back, and shows its state in a floating companion window.

Current focus:
- hands-free desktop control
- bilingual interaction in English and Hindi
- local plus cloud AI routing
- live conversational follow-ups
- companion-style desktop interaction

## What VOXIS Can Do Today

### Voice and Conversation
- Wake with `Jarvis` or `Voxis`
- Stay in live conversation mode for follow-up commands without repeating the wake word every turn
- Speak responses back using Windows TTS
- Switch between English and Hindi modes
- Switch AI modes by voice:
  - `local`
  - `gemini`
  - `groq`
  - `auto`

### Desktop Actions
- Open common desktop apps and web apps
- Handle common system shortcuts
- Control volume
- Scroll and navigate
- Take screenshots
- Read or summarize the screen
- Answer local system-information questions
- Do basic calculator-style math
- Keep short-term context for follow-up commands

### Gesture Control
- open-palm activation
- one-finger cursor movement
- pinch click
- pinch drag/select
- two-finger scroll
- three-finger screenshot
- fist play/pause

### Interface
- Floating always-on-top companion window
- Shows:
  - live transcript
  - current status
  - current language
  - current AI mode

## Current Architecture

The project is moving away from a monolithic voice engine into a generic action pipeline:

`input -> intent -> context -> plan -> execute -> respond`

### Active Runtime Modules
- `main.py`
- `core/voice_runtime.py`
- `core/orchestrator.py`
- `core/intent_parser.py`
- `core/action_registry.py`
- `core/model_router.py`
- `core/ai_brain_runtime.py`
- `core/context_manager.py`
- `core/state.py`
- `core/speaker.py`
- `core/listener.py`
- `core/companion_window.py`
- `core/gesture_engine.py`
- `core/screen_vision.py`

Legacy files like `core/voice_engine.py` and `core/ai_brain.py` still exist in the repo, but the current runtime path uses `voice_runtime.py` and `ai_brain_runtime.py`.

## Tech Stack

- Python 3.x
- MediaPipe
- OpenCV
- PyAutoGUI
- SpeechRecognition
- pyttsx3
- Tkinter
- Ollama / local LLM
- Google Gemini API
- Groq API

## Running VOXIS

From the project root:

```powershell
.\voxis_env\Scripts\Activate.ps1
python main.py
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\voxis_env\Scripts\Activate.ps1
python main.py
```

You can also run directly with the venv Python:

```powershell
.\voxis_env\Scripts\python.exe main.py
```

## Configuration

VOXIS loads settings from:

```text
config/settings.py
```

Important values include:
- `AI_MODE`
- `LOCAL_MODEL`
- `GROQ_MODEL`
- `GEMINI_MODEL`
- `PRIMARY_LANGUAGE`
- `FALLBACK_LANGUAGE`
- `VOICE_SPEED`
- `VOICE_VOLUME`

Do not commit real API keys to a public repository.

## Example Commands

### English
- `Jarvis open calculator`
- `open youtube`
- `give me my system information`
- `switch to gemini`
- `switch to local`
- `read my screen`
- `add 23 and 45`

### Hindi
- `camera kholo`
- `calculator kholo`
- `settings kholo`
- `volume badhao`
- `hindi mode`

## Known Limitations

- Hindi speech output depends on a Hindi voice being installed in Windows
- `requirements.txt` is still incomplete
- The runtime is Windows-oriented right now
- Workflow automation is still early-stage
- The floating UI is a minimal first version
- Some files in the repo are placeholders or legacy modules

## What Has Been Added Recently

- Generic voice runtime
- Structured intent parsing
- Context-aware command handling
- Live conversation mode
- Floating companion window
- System information action
- Voice-controlled AI mode switching
- Hindi app-name normalization for common commands
- Windows speech output improvements

## Project Direction

VOXIS is being built as:

`a real-time AI collaborator that can talk, think, and act across your system while you are using it`

Long-term direction:
- accessibility-first hands-free interaction
- desktop copilot workflows
- better local memory
- smoother multimodal interaction
- stronger real-time autonomy

## Status

Active development.

Current stage:
- working prototype
- architecture refactor in progress
- moving toward a more reliable companion-style desktop product
