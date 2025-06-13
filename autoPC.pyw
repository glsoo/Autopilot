import os
import time
import io
import base64
import re
import pyautogui
import keyboard
from PIL import ImageGrab
from openai import OpenAI
import tkinter as tk
from tkinter import simpledialog, messagebox, scrolledtext

# ==== CONFIG LOADING ====

CONFIG_FILE = "config.txt"
config = {
    "API_KEY": "",
    "MODEL": "gpt-4o",
    "MAX_TOKENS": "400",
    "MAX_ITERATIONS": "100",
    "SCREEN_X": "1920",
    "SCREEN_Y": "1080",
    "DEFAULT_EXIT_MESSAGE": "Objective complete."
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    if k in config:
                        config[k] = v.strip()
    if not config["API_KEY"]:
        root = tk.Tk()
        root.withdraw()
        key = simpledialog.askstring("API Key Needed", "Enter your OpenAI API Key: (save it somewhere)",)
        root.destroy()
        if key:
            config["API_KEY"] = key.strip()
            save_config()
        else:
            messagebox.showerror("Missing Key", "❌ API Key required to continue.")
            exit()

def save_config():
    with open(CONFIG_FILE, "w") as f:
        for k, v in config.items():
            f.write(f"{k}={v}\n")

load_config()

# Apply config values
api_key = config["API_KEY"]
model = config["MODEL"]
max_iterations = int(config["MAX_ITERATIONS"])
screen_x = int(config["SCREEN_X"])
screen_y = int(config["SCREEN_Y"])
default_exit_message = config["DEFAULT_EXIT_MESSAGE"]
tokens = config["MAX_TOKENS"]
client = OpenAI(api_key=api_key)

# ==== GUI OBJECTIVE INPUT (MULTILINE) ====

def get_objective():
    def on_submit():
        nonlocal text_input, root
        root.result = text_input.get("1.0", "end").strip()
        root.quit()
        root.destroy()

    root = tk.Tk()
    root.title("Enter Objective")
    root.geometry("500x300")
    tk.Label(root, text="What is your objective? Be as detailed as possible.").pack(pady=5)
    text_input = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=10)
    text_input.pack(padx=10, pady=5)
    tk.Button(root, text="Start Autopilot", command=on_submit).pack(pady=10)
    root.mainloop()
    return getattr(root, "result", "").strip()

objective = get_objective()
if not objective:
    print("❌ No objective provided. Exiting.")
    exit()

# ==== SCREEN + COLOR HELPERS ====

def take_screenshot():
    return ImageGrab.grab()

def image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def hex_to_rgb(hex_code):
    hex_code = hex_code.lstrip("#")
    return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))

def find_pixel_by_color(image, target_rgb, region='any', tolerance=20):
    width, height = image.size
    pixels = image.load()

    def in_region(x, y):
        if region == 'top_left': return x < width // 2 and y < height // 2
        if region == 'top_right': return x >= width // 2 and y < height // 2
        if region == 'bottom_left': return x < width // 2 and y >= height // 2
        if region == 'bottom_right': return x >= width // 2 and y >= height // 2
        if region == 'center': return width // 4 < x < 3 * width // 4 and height // 4 < y < 3 * height // 4
        return True

    for y in range(0, height, 2):
        for x in range(0, width, 2):
            if in_region(x, y):
                r, g, b = pixels[x, y][:3]
                if all(abs(c1 - c2) <= tolerance for c1, c2 in zip((r, g, b), target_rgb)):
                    return (x, y)
    return None

def click_color(hex_code):
    img = ImageGrab.grab()
    loc = find_pixel_by_color(img, hex_to_rgb(hex_code))
    if loc:
        pyautogui.moveTo(*loc, duration=0.2)
        pyautogui.click()

def click_color_near(hex_code, region="center"):
    img = ImageGrab.grab()
    loc = find_pixel_by_color(img, hex_to_rgb(hex_code), region=region)
    if loc:
        pyautogui.moveTo(*loc, duration=0.2)
        pyautogui.click()

def hover_color(hex_code, region="any", duration=0.2):
    img = ImageGrab.grab()
    loc = find_pixel_by_color(img, hex_to_rgb(hex_code), region=region)
    if loc:
        pyautogui.moveTo(*loc, duration=duration)

def scroll_until_color(hex_code, direction="down", max_attempts=10, region='any', tolerance=20, scroll_amount=300):
    rgb = hex_to_rgb(hex_code)
    for _ in range(max_attempts):
        img = ImageGrab.grab()
        loc = find_pixel_by_color(img, rgb, region=region, tolerance=tolerance)
        if loc:
            pyautogui.moveTo(*loc, duration=0.2)
            pyautogui.click()
            return True
        pyautogui.scroll(-scroll_amount if direction == "down" else scroll_amount)
        time.sleep(0.5)
    return False

# ==== AI INTEGRATION ====

def clean_gpt_code(code: str) -> str:
    return re.sub(r"^```(?:python)?\s*|```$", "", code.strip(), flags=re.IGNORECASE).strip()

def ask_gpt(image, prompt="What should I do next? Respond ONLY with valid Python function calls. No explanation."):
    img_b64 = image_to_base64(image)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a robotic assistant that sees screenshots and controls the computer using Python.\n"
                    f"Screen Size: {screen_x}x{screen_y}\n"
                    f"Objective: {objective}\n"
                    "Allowed functions:\n"
                    "- pyautogui.moveTo(x, y, duration=required)\n"
                    "- pyautogui.click(x, y)\n"
                    "- pyautogui.rightClick(x, y)\n"
                    "- pyautogui.scroll(amount)\n"
                    "- pyautogui.write('text')\n"
                    "- pyautogui.press('key')\n"
                    "- pyautogui.hotkey('key1', 'key2', ...)\n"
                    "- click_color('#RRGGBB')\n"
                    "- click_color_near('#RRGGBB', region='top_left'|'center'|'bottom_right')\n"
                    "- hover_color('#RRGGBB', region='top_left'|'center'|'bottom_right')\n"
                    "- scroll_until_color('#RRGGBB', direction='down'|'up', max_attempts=10)\n"
                    "- exit('message')  # Call this when the task is complete."
                )
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
                ]
            }
        ],
        max_tokens=tokens
    )
    content = response.choices[0].message.content
    if "I'm sorry" in content or "I can't assist" in content:
        return ""
    return clean_gpt_code(content)

# ==== SAFE EXECUTION ====

out = default_exit_message

def customExit(output=None):
    global out
    out = output or default_exit_message
    raise StopIteration

def safe_execute(multiline_code: str):
    lines = multiline_code.strip().splitlines()
    for i, line in enumerate(lines):
        if keyboard.is_pressed("f5"):
            print(f"\n🛑 F5 pressed. Stopping before line {i+1}.")
            break
        try:
            safe_globals = {
                "pyautogui": pyautogui,
                "click_color": click_color,
                "click_color_near": click_color_near,
                "hover_color": hover_color,
                "scroll_until_color": scroll_until_color,
                "keyboard": keyboard,
                "time": time,
                "exit": customExit,
            }
            exec(line.strip(), safe_globals)
            time.sleep(0.3)
        except StopIteration:
            raise
        except Exception as e:
            print(f"[!] Error in line {i+1}: {e}")

# ==== MAIN LOOP ====

def main():
    try:
        for step in range(max_iterations):
            if keyboard.is_pressed("f5"):
                break
            screenshot = take_screenshot()
            code = ask_gpt(screenshot)
            if code.strip():
                safe_execute(code)
            for _ in range(20):
                if keyboard.is_pressed("f5"):
                    return
                time.sleep(0.1)
    except StopIteration:
        messagebox.showinfo("AI Autopilot", f"✅ {out}")
    except KeyboardInterrupt:
        print("\n🛑 Manual interrupt. Exiting.")

if __name__ == "__main__":
    main()
