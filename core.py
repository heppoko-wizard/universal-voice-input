import os
import sys
import tempfile
import threading
import subprocess
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from pynput import keyboard
import time
import config_manager
import platform_utils
from transcriber import Transcriber

# Global State
is_recording = False
audio_data = []
stream = None
config = config_manager.load_config()
transcriber_instance = Transcriber(config)

def audio_callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    if is_recording:
        audio_data.append(indata.copy())

def start_recording():
    global is_recording, audio_data, stream, config, transcriber_instance
    if is_recording:
        return

    # Reload config
    config = config_manager.load_config()
    transcriber_instance.reload_config(config)
    
    print("--- Starting Recording ---")
    platform_utils.play_sound("start")
    platform_utils.notify("STT Recording", "STARTED...")
    
    # Pre-load model in background if transient mode
    threading.Thread(target=transcriber_instance.prepare_model).start()
    
    audio_data = [] 
    is_recording = True
    
    try:
        # Resolve device_id (index or pulse source name)
        device_id = config.get("device_index")
        samplerate = config.get("sample_rate", 44100)
        
        # Handle PulseAudio source names (Linux specific, but harmless logic if handled safely)
        if isinstance(device_id, str) and device_id.startswith("alsa_input.") and platform_utils.get_platform() == "linux":
            print(f"Selecting PulseAudio Source: {device_id}")
            os.environ["PULSE_SOURCE"] = device_id
            # Find the 'pulse' device index
            devices = sd.query_devices()
            for i, d in enumerate(devices):
                if 'pulse' in d['name'].lower():
                    device_id = i
                    break
        
        if device_id is not None and not isinstance(device_id, int):
             device_id = None
             
        if device_id is not None:
             try:
                 dev_info = sd.query_devices(device_id)
                 print(f"Using Device: [{device_id}] {dev_info['name']}")
             except Exception:
                 device_id = None # Fallback

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
        platform_utils.play_sound("error")
        is_recording = False

def stop_and_transcribe():
    global is_recording, stream
    if not is_recording:
        return

    print("--- Stopping Recording ---")
    is_recording = False
    
    platform_utils.notify("STT Recording", "STOPPED (Processing...)")

    if stream:
        try:
            stream.stop()
            stream.close()
        except Exception:
            pass
    
    platform_utils.play_sound("stop")
    threading.Thread(target=process_audio).start()

def process_audio():
    global config, transcriber_instance
    print("Processing audio...")
    if not audio_data:
        return

    recording = np.concatenate(audio_data, axis=0)
    samplerate = config.get("sample_rate", 44100)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
        temp_filename = tmp_file.name
        data_int16 = (recording * 32767).astype(np.int16)
        write(temp_filename, samplerate, data_int16)
    
    # Process for Speed Up (Time Compression)
    speed_factor = config.get("speed_factor", 2.0)
    final_filename = temp_filename
    
    if speed_factor > 1.05 and platform_utils.get_platform() == "linux": # Check ffmpeg availability?
        # TODO: Add cross-platform ffmpeg check or pure python speedup
        # For now, keep existing logic but wrapped in try
        try:
             # Basic FFmpeg check
             if subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
                print(f"Applying speed up x{speed_factor}...")
                processed_filename = temp_filename.replace(".wav", "_fast.wav")
                subprocess.run([
                    "ffmpeg", "-y", "-i", temp_filename,
                    "-filter:a", f"atempo={speed_factor}",
                    "-vn", processed_filename
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                final_filename = processed_filename
                print(f"Speed up applied. New file: {final_filename}")
        except Exception as e:
            print(f"Speedup failed: {e}. Using original audio.")
    
    try:
        text = transcriber_instance.transcribe(final_filename)
        
        if text:
            type_text(text)
        else:
            print("Transcription failed.")
            platform_utils.play_sound("error")
            
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
        if final_filename != temp_filename and os.path.exists(final_filename):
            os.remove(final_filename)

def type_text(text):
    print(f"Typing: {text}")
    try:
        platform_utils.copy_text(text)
        time.sleep(0.3)
        platform_utils.paste_text()
            
    except Exception as e:
        print(f"Error typing text: {e}")

def on_toggle():
    if is_recording:
        stop_and_transcribe()
    else:
        start_recording()

def main():
    print("Speech-to-Text Core Running...")
    print(f"Platform: {platform_utils.get_platform()}")
    
    if config.get("device_index") is not None:
        print(f"Manual device configured: Index {config.get('device_index')}")
    else:
        print("Using OS default input device.")

    # Parse hotkey
    hotkey_str = config.get("hotkey", "<ctrl>+<alt>+<space>")
    hotkey_str = platform_utils.get_hotkey_map(hotkey_str)
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
