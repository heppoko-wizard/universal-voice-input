import json
import os
import sounddevice as sd

# プロジェクトルートディレクトリを取得し、絶対パスで config.json を指定
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(PROJECT_ROOT, "config.json")

DEFAULT_CONFIG = {
    "api_order": ["groq", "openai"],
    "api_keys": {
        "groq": "",
        "openai": "",
        "google": ""
    },
    "device_index": None, # None means default
    "default_device_index": None, # ユーザーが明示的に選んだデフォルト
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
    try:
        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            if dev['max_input_channels'] > 0:
                input_devices.append({"id": i, "name": dev['name']})
    except Exception:
        pass
            
    return input_devices
