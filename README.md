# USE THIS AT YOUR OWN RISK.
# CONFIG.TXT REQUIRED.

# Autopilot



**Autopilot** is a desktop automation tool that uses GPT-4 and screen analysis to execute user-defined tasks. It captures your screen, understands your objective, and automates your computer through intelligent actions.

---

## Features

- Multi-line input for detailed task objectives
- Real-time screen capture and AI interpretation
- Executes actions including:
  - Mouse movement and clicks
  - Key presses and typing
  - Scrolling
  - Color-based detection and interaction
- Custom functions for clicking by color and region
- F5 key to instantly stop execution
- Success message appears when the task completes
- All settings configurable via `config.txt`

---

## Configuration (Required)

Autopilot requires a `config.txt` file in the same folder as the executable.

If this file is missing, the program will not start.

### Example `config.txt`:
```
API_KEY=
MODEL=gpt-4o
MAX_ITERATIONS=100
SCREEN_X=1920
SCREEN_Y=1080
DEFAULT_EXIT_MESSAGE=Objective complete.
```

- If no API key is found, you will be prompted to enter one.
- All other values are optional and can be adjusted as needed.

---

## Usage

1. Run `Autopilot.exe`
2. Enter your task or objective in the input window
3. Autopilot will begin interpreting your screen and taking actions
4. Press `F5` at any time to stop
5. A message will display when the task is marked complete by the AI

---

## Disclaimer

**Use this software at your own risk.**

- Autopilot can control your mouse and keyboard automatically.
- The developer is **not responsible** for any unintended behavior, file changes, system actions, or data loss.
- Always run in a controlled environment and review objectives before submitting.

---

## Version

**v1.0 - Initial Release**
