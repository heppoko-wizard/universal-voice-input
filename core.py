import os
import sys
import tempfile
import threading
import subprocess
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from groq import Groq
from openai import OpenAI
from pynput import keyboard
import time
import config_manager

# Global State
is_recording = False
audio_data = []
stream = None
config = config_manager.load_config()

def play_sound(sound_type="start"):
    """Plays a feedback sound if available."""
    sounds = {
        "start": "/usr/share/sounds/freedesktop/stereo/camera-shutter.oga",
        "stop": "/usr/share/sounds/freedesktop/stereo/complete.oga",
        "error": "/usr/share/sounds/freedesktop/stereo/dialog-warning.oga"
    }
    path = sounds.get(sound_type)
    if path and os.path.exists(path):
        subprocess.Popen(["paplay", path], stderr=subprocess.DEVNULL)

def audio_callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    if is_recording:
        audio_data.append(indata.copy())

def start_recording():
    global is_recording, audio_data, stream, config
    if is_recording:
        return

    # Reload config to get latest changes
    config = config_manager.load_config()
    
    print("--- Starting Recording ---")
    play_sound("start")
    audio_data = [] 
    is_recording = True
    
    try:
        device_id = config.get("device_index")
        samplerate = config.get("sample_rate", 44100)
        
        # If device_id is not valid integer, set to None (default)
        if device_id is not None and not isinstance(device_id, int):
             device_id = None

        stream = sd.InputStream(
            device=device_id,
            samplerate=samplerate,
            channels=1,
            callback=audio_callback,
            blocksize=1024
        )
        stream.start()
    except Exception as e:
        print(f"Error starting stream: {e}")
        play_sound("error")
        is_recording = False

def stop_and_transcribe():
    global is_recording, stream
    if not is_recording:
        return

    print("--- Stopping Recording ---")
    is_recording = False
    if stream:
        try:
            stream.stop()
            stream.close()
        except Exception:
            pass
    
    play_sound("stop")
    threading.Thread(target=process_audio).start()

def process_audio():
    global config
    print("Processing audio...")
    if not audio_data:
        return

    recording = np.concatenate(audio_data, axis=0)
    samplerate = config.get("sample_rate", 44100)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
        temp_filename = tmp_file.name
        data_int16 = (recording * 32767).astype(np.int16)
        write(temp_filename, samplerate, data_int16)
    
    text = None
    try:
        # Try APIs in order
        for api_name in config["api_order"]:
            api_key = config["api_keys"].get(api_name)
            if not api_key:
                continue
                
            print(f"Trying API: {api_name}...")
            try:
                if api_name == "groq":
                    text = transcribe_groq(temp_filename, api_key)
                elif api_name == "openai":
                    text = transcribe_openai(temp_filename, api_key)
                # Add Google fallback here later
                
                if text:
                    break # Success
            except Exception as e:
                print(f"API {api_name} failed: {e}")
                continue

        if text:
            type_text(text)
        else:
            print("All APIs failed.")
            play_sound("error")
            
    finally:
        os.remove(temp_filename)

def transcribe_groq(filename, api_key):
    client = Groq(api_key=api_key)
    with open(filename, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=(filename, file.read()),
            model="whisper-large-v3",
            response_format="text",
            language=config.get("language", "ja")
        )
    return transcription.strip()

def transcribe_openai(filename, api_key):
    client = OpenAI(api_key=api_key)
    with open(filename, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=file,
            model="whisper-1",
            response_format="text",
            language=config.get("language", "ja")
        )
    return transcription.strip()

def type_text(text):
    print(f"Typing: {text}")
    try:
        original_content = None
        if config.get("clipboard_restore", True):
            try:
                original_content = subprocess.check_output(["xclip", "-selection", "clipboard", "-o"], stderr=subprocess.DEVNULL)
            except Exception:
                pass

        import pyperclip
        if os.system("xclip -version > /dev/null 2>&1") == 0:
             os.environ['PYPERCLIP_BACKEND'] = 'xclip'
        
        pyperclip.copy(text)
        time.sleep(0.3)
        subprocess.run(["xdotool", "key", "--clearmodifiers", "ctrl+v"])
        time.sleep(0.2)
        
        if original_content is not None:
            process = subprocess.Popen(["xclip", "-selection", "clipboard", "-i"], stdin=subprocess.PIPE)
            process.communicate(input=original_content)
        elif config.get("clipboard_restore", True):
             subprocess.run(["xclip", "-selection", "clipboard", "/dev/null"], stderr=subprocess.DEVNULL)
            
    except Exception as e:
        print(f"Error typing text: {e}")

def on_toggle():
    if is_recording:
        stop_and_transcribe()
    else:
        start_recording()

def main():
    print("Speech-to-Text Core Running...")
    
    # Parse hotkey from config or default
    hotkey_str = config.get("hotkey", "<ctrl>+<alt>+<space>")
    print(f"Hotkey: {hotkey_str}")

    try:
        with keyboard.GlobalHotKeys({
            hotkey_str: on_toggle
        }) as h:
            h.join()
    except ValueError:
        print(f"Invalid hotkey: {hotkey_str}. Using default.")
        with keyboard.GlobalHotKeys({
            '<ctrl>+<alt>+<space>': on_toggle
        }) as h:
            h.join()

if __name__ == "__main__":
    main()
