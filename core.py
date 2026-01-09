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
overlay_process = None
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

def check_microphone_level(device_id, samplerate=44100, duration=0.25):
    """Checks the RMS amplitude of a microphone device."""
    try:
        # Check if device supports the requested samplerate
        try:
            sd.check_input_settings(device=device_id, channels=1, samplerate=samplerate)
        except Exception:
            # Fallback to device's default samplerate if 44100 fails
            dev_info = sd.query_devices(device_id)
            samplerate = int(dev_info['default_samplerate'])
        
        recording = sd.rec(
            int(duration * samplerate), 
            samplerate=samplerate, 
            channels=1, 
            device=device_id, 
            dtype='float32',
            blocking=True
        )
        rms = np.sqrt(np.mean(recording**2))
        return rms
    except Exception as e:
        # print(f"  Device {device_id} error: {e}")
        return -1.0

def auto_select_microphone():
    """Scans all input devices and returns the index of the one with the highest input level."""
    print("\n--- Auto-selecting Microphone ---")
    print("Testing all input devices for audio signal...")
    
    devices = sd.query_devices()
    best_device = None
    max_rms = -1.0
    
    # Threshold to consider as "active" signal (silence is usually near 0)
    # 0.001 is a conservative threshold for silence/noise floor
    SILENCE_THRESHOLD = 0.001

    for i, device in enumerate(devices):
        # Skip output-only devices
        if device['max_input_channels'] <= 0:
            continue
            
        # Skip some virtual devices or monitors if possible to avoid loops (optional heuristic)
        # For now, we test everything that has input channels.
        
        print(f"Testing device [{i}] {device['name']}...", end="", flush=True)
        rms = check_microphone_level(i)
        
        if rms >= 0:
            print(f" Level: {rms:.6f}")
        else:
            print(" Failed to read.")

        if rms > max_rms:
            max_rms = rms
            best_device = i
    
    if best_device is not None and max_rms > SILENCE_THRESHOLD:
        print(f"\n>>> Selected Device [{best_device}]: {devices[best_device]['name']} (Peak Level: {max_rms:.6f})")
        return best_device
    
    print("\n>>> No active signal detected above threshold. Falling back to default.")
    return None

# Global detected device
detected_device_id = None

def start_recording():
    global is_recording, audio_data, stream, config, detected_device_id, overlay_process
    if is_recording:
        return

    # Reload config to get latest changes
    config = config_manager.load_config()
    
    print("--- Starting Recording ---")
    play_sound("start")
    
    # Start Overlay
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        overlay_script = os.path.join(script_dir, "overlay.py")
        overlay_process = subprocess.Popen([sys.executable, overlay_script], stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"Failed to start overlay: {e}")

    audio_data = [] 
    is_recording = True
    
    try:
        # Use detected device if available, otherwise config, otherwise None (OS default)
        device_id = detected_device_id if detected_device_id is not None else config.get("device_index")
        samplerate = config.get("sample_rate", 44100)
        
        # If device_id is not valid integer, set to None (default)
        if device_id is not None and not isinstance(device_id, int):
             device_id = None
             
        if device_id is not None:
             dev_info = sd.query_devices(device_id)
             print(f"Using Device: [{device_id}] {dev_info['name']}")

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
        if overlay_process:
            overlay_process.terminate()
            overlay_process = None

def stop_and_transcribe():
    global is_recording, stream, overlay_process
    if not is_recording:
        return

    print("--- Stopping Recording ---")
    is_recording = False
    
    # Stop Overlay
    if overlay_process:
        overlay_process.terminate()
        overlay_process = None

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
    
    # Process for Speed Up (Time Compression)
    speed_factor = config.get("speed_factor", 2.0)
    final_filename = temp_filename
    
    if speed_factor > 1.05: # Allow small margin
        print(f"Applying speed up x{speed_factor}...")
        processed_filename = temp_filename.replace(".wav", "_fast.wav")
        try:
            # Use ffmpeg to speed up audio without changing pitch (atempo)
            # atempo filter supports 0.5 to 2.0. For higher speeds, we need to chain them.
            # But simple 2.0 is common. Let's handle up to 2.0 simply.
            # If user sets 3.0, we might need multiple passes or simple rate change.
            # For speech recognition, 'atempo' is best.
            
            # Construct filter chain for > 2.0 support if needed, but let's stick to simple first.
            # atempo limit is actually 100.0 in recent ffmpeg, but used to be 2.0.
            # Let's assume modern ffmpeg.
            
            subprocess.run([
                "ffmpeg", "-y", "-i", temp_filename,
                "-filter:a", f"atempo={speed_factor}",
                "-vn", processed_filename
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            
            # If successful, use the processed file
            final_filename = processed_filename
            print(f"Speed up applied. New file: {final_filename}")
        except Exception as e:
            print(f"FFmpeg speedup failed: {e}. Using original audio.")
    
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
                    text = transcribe_groq(final_filename, api_key)
                elif api_name == "openai":
                    text = transcribe_openai(final_filename, api_key)
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
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
        if final_filename != temp_filename and os.path.exists(final_filename):
            os.remove(final_filename)

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
    global detected_device_id
    print("Speech-to-Text Core Running...")
    
    # Check config for manually selected device
    # If "device_index" is None, it means "Default" in GUI, so we try auto-detect.
    # But wait, usually "Default" means OS Default. 
    # Let's assume if user explicitly wants auto-magic, we might need a flag, 
    # but for now, let's treat "Default" (None) as "Try to find the best one".
    # OR, if you prefer, only auto-detect if explicitly requested. 
    # Based on user request: "Auto select only when... user set to default/auto"
    
    # If config has a specific integer index, respect it.
    # If config is None, run auto-select.
    
    if config.get("device_index") is None:
        detected_device_id = auto_select_microphone()
    else:
        print(f"Manual device configured: Index {config.get('device_index')}")
        detected_device_id = None # Will use config['device_index'] in start_recording

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
