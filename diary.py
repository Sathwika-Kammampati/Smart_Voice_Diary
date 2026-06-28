import os
import queue
import sounddevice as sd
import json
from vosk import Model, KaldiRecognizer
from datetime import datetime
import language_tool_python
import sys

# Load Vosk model (make sure folder name is "model")
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

model_path = os.path.join(base_path, "model")
model = Model(model_path)
recognizer = KaldiRecognizer(model, 16000)

q = queue.Queue()

# Microphone callback
def callback(indata, frames, time, status):
    if status:
        print(status)
    q.put(bytes(indata))

print("🎤 Start speaking...")
print("Say 'stop' to finish.\n")

full_text = ""

# Start recording
with sd.RawInputStream(
        samplerate=16000,
        blocksize=8000,
        dtype='int16',
        channels=1,
        callback=callback):

    while True:
        data = q.get()
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            text = result.get("text", "")

            if text:
                print("You said:", text)
                full_text += " " + text

                # Stop condition
                if "stop" in text.lower():
                    print("\n🛑 Stopping diary recording...")
                    break


# ---------------- NLP + GRAMMAR CORRECTION ----------------

# Remove stop command
full_text = full_text.lower().replace("stop diary", "")
full_text = full_text.strip()

# Capitalize first letter
if full_text:
    full_text = full_text.capitalize()

# Initialize grammar tool
tool = language_tool_python.LanguageTool('en-US')

# Apply grammar correction
corrected_text = tool.correct(full_text)

# Ensure period at end
if corrected_text and not corrected_text.endswith("."):
    corrected_text += "."

# ---------------- SAVE FILE ----------------

now = datetime.now()
date_str = now.strftime("%d-%m-%Y")
time_str = now.strftime("%I:%M %p")
filename_time = now.strftime("%Y-%m-%d_%H-%M-%S")

# Create diary_entries folder if not exists
if not os.path.exists("diary_entries"):
    os.makedirs("diary_entries")

filename = f"diary_entries/diary_{filename_time}.txt"

with open(filename, "w", encoding="utf-8") as file:
    file.write(f"Date: {date_str}\n")
    file.write(f"Time: {time_str}\n\n")
    file.write(corrected_text)

print(f"\n✅ Diary saved successfully as:\n{filename}")