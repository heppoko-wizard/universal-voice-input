import os
import sys
import queue
import tempfile
import threading
import subprocess
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from groq import Groq
from pynput import keyboard
from dotenv import load_dotenv
import time

# Load configuration
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    print("Error: GROQ_API_KEY not found. Please set it in .env file.")
    sys.exit(1)

client = Groq(api_key=API_KEY)

# Audio Configuration
SAMPLE_RATE = 48000
CHANNELS = 1
BLOCK_SIZE = 1024

# Global State
is_recording = False
audio_data = []
stream = None

def get_blue_yeti_device_id():
    """Finds the device ID for Blue Yeti."""
    try:
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if "Blue Microphones" in device['name'] and device['max_input_channels'] > 0:
                print(f"Found Blue Yeti at device ID {i}")
                return i
    except Exception as e:
        print(f"Error querying devices: {e}")
    print("Blue Yeti not found, using default device.")
    return None

def play_sound(sound_type="start"):
    """Plays a feedback sound if available."""
    # Common sounds on Kubuntu/KDE
    sounds = {
        "start": "/usr/share/sounds/freedesktop/stereo/camera-shutter.oga",
        "stop": "/usr/share/sounds/freedesktop/stereo/complete.oga"
    }
    path = sounds.get(sound_type)
    if path and os.path.exists(path):
        subprocess.Popen(["paplay", path], stderr=subprocess.DEVNULL)
    else:
        print(f"[{sound_type.upper()}] (Sound file not found)")

def audio_callback(indata, frames, time, status):
    """Callback for sounddevice to capture audio."""
    if status:
        print(status, file=sys.stderr)
    if is_recording:
        audio_data.append(indata.copy())

def start_recording():
    global is_recording, audio_data, stream
    if is_recording:
        return

    print("--- Starting Recording ---")
    play_sound("start")
    audio_data = [] # Reset buffer
    is_recording = True
    
    device_id = get_blue_yeti_device_id()
    
    # Start the stream
    stream = sd.InputStream(
        device=device_id,
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        callback=audio_callback,
        blocksize=BLOCK_SIZE
    )
    stream.start()

def stop_and_transcribe():
    global is_recording, stream
    if not is_recording:
        return

    print("--- Stopping Recording ---")
    is_recording = False
    if stream:
        stream.stop()
        stream.close()
    
    play_sound("stop")
    
    # Process audio in a separate thread to not block the input listener
    threading.Thread(target=process_audio).start()

def process_audio():
    print("Processing audio...")
    if not audio_data:
        print("No audio recorded.")
        return

    # Concatenate all audio blocks
    recording = np.concatenate(audio_data, axis=0)
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
        temp_filename = tmp_file.name
        # Scale to 16-bit integer (scipy requirement for WAV)
        # sounddevice returns float32 by default in range [-1, 1]
        data_int16 = (recording * 32767).astype(np.int16)
        write(temp_filename, SAMPLE_RATE, data_int16)
    
    try:
        print("Sending to Groq API...")
        start_time = time.time()
        
        with open(temp_filename, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(temp_filename, file.read()),
                model="whisper-large-v3",
                response_format="text",
                language="ja" # Specify Japanese for better accuracy
            )
        
        text = transcription.strip()
        elapsed = time.time() - start_time
        print(f"Transcription ({elapsed:.2f}s): {text}")
        
        if text:
            type_text(text)
            
    except Exception as e:
        print(f"Error during transcription: {e}")
    finally:
        os.remove(temp_filename)

def type_text(text):
    """Types the text using xdotool and restores clipboard content."""
    print(f"Typing: {text}")
    try:
        # Save original clipboard content
        # -selection clipboard -o returns current clipboard
        original_content = None
        try:
            original_content = subprocess.check_output(["xclip", "-selection", "clipboard", "-o"], stderr=subprocess.DEVNULL)
        except Exception:
            pass # No text content in clipboard

        # Copy new text to clipboard
        import pyperclip
        # Force xclip backend to avoid Klipper error
        if os.system("xclip -version > /dev/null 2>&1") == 0:
             os.environ['PYPERCLIP_BACKEND'] = 'xclip'
        
        pyperclip.copy(text)
        
        # Wait a tiny bit for clipboard to update
        time.sleep(0.3)
        
        # Simulate Ctrl+V
        subprocess.run(["xdotool", "key", "--clearmodifiers", "ctrl+v"])
        
        # Wait for paste to finish before restoring
        time.sleep(0.2)
        
        # Restore original clipboard content
        if original_content is not None:
            process = subprocess.Popen(["xclip", "-selection", "clipboard", "-i"], stdin=subprocess.PIPE)
            process.communicate(input=original_content)
        else:
            # Clear if it was empty
            subprocess.run(["xclip", "-selection", "clipboard", "/dev/null"], stderr=subprocess.DEVNULL)
            
    except Exception as e:
        print(f"Error typing text: {e}")

def on_toggle():
    if is_recording:
        stop_and_transcribe()
    else:
        start_recording()

def main():
    print("Groq Speech-to-Text Tool Running...")
    print("Press 'Ctrl + Alt + Space' to toggle recording.")
    print("Logs will appear here.")
    
    # Setup global hotkey
    # <ctrl>+<alt>+<space>
    with keyboard.GlobalHotKeys({
        '<ctrl>+<alt>+<space>': on_toggle
    }) as h:
        h.join()

if __name__ == "__main__":
    main()
