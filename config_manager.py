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
    "clipboard_restore": True
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
    try:
        devices = sd.query_devices()
        input_devices = []
        for i, dev in enumerate(devices):
            if dev['max_input_channels'] > 0:
                input_devices.append({"id": i, "name": dev['name']})
        return input_devices
    except Exception:
        return []
