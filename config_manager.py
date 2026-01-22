import json
import os
import sounddevice as sd

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "api_order": ["groq", "openai"],
    "api_keys": {
        "groq": "",
        "openai": "",
        "google": ""
    },
    "device_index": None, # None means default
    "sample_rate": 44100,
    "language": "ja",
    "hotkey": "<ctrl>+<alt>+<space>",
    "clipboard_restore": True,
    "use_local_model": True,
    "local_model_id": "RoachLin/kotoba-whisper-v2.2-faster",
    "local_device": "cuda",
    "local_compute_type": "int8",
    "local_always_loaded": True,
    "local_ram_cache": False
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            # Merge with default to ensure all keys exist
            for key, value in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = value
            return config
    except Exception:
        return DEFAULT_CONFIG

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def get_input_devices():
    input_devices = []
    
    # 1. Try PortAudio (sounddevice)
    try:
        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            if dev['max_input_channels'] > 0:
                input_devices.append({"id": i, "name": dev['name']})
    except Exception:
        pass

    # 2. Try PulseAudio (pactl) as fallback/supplement for Linux
    if os.name == 'posix':
        try:
            import subprocess
            cmd = "LANG=C pactl list sources | grep -E 'Name:|Description:'"
            output = subprocess.check_output(cmd, shell=True).decode()
            
            lines = output.splitlines()
            for i in range(0, len(lines), 2):
                if i + 1 < len(lines):
                    name = lines[i].split("Name: ")[1].strip()
                    desc = lines[i+1].split("Description: ")[1].strip()
                    
                    # Avoid duplicates and monitor devices
                    if not name.endswith(".monitor") and not any(d['name'] == desc for d in input_devices):
                        input_devices.append({"id": name, "name": f"[Pulse] {desc}"})
        except Exception:
            pass
            
    return input_devices
