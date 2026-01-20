#!/usr/bin/env python3
"""
STT Worker - One-Shot Mode (Zero/CPU)

このスクリプトは、Zero Memory / CPU Preread モード用の使い捨てワーカーです。
- 起動 -> モデルロード -> 録音 -> 文字起こし -> 終了
- プロセス終了によりVRAMを確実に解放します
"""
import time
original_start_time = time.time()
print(f"[PROFILER] Script Start: {0:.4f}")

import os
import sys
import signal
import threading
import queue
import numpy as np
import sounddevice as sd
import config_manager
import logging
import platform_utils

print(f"[PROFILER] Basic Imports Done: {time.time() - original_start_time:.4f}")

# Configure Logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("stt_worker")

# Global flags
stop_event = threading.Event()
recording_finished_event = threading.Event()
audio_queue = queue.Queue()

# Configuration
config = config_manager.load_config()
print(f"[PROFILER] Config Loaded: {time.time() - original_start_time:.4f}")

MODEL_PATH = config.get("local_model_size", "models/kotoba-whisper-v2.2-int8")
DEVICE = config.get("local_device", "cuda")
COMPUTE_TYPE = config.get("local_compute_type", "int8")
SAMPLE_RATE = config.get("sample_rate", 16000)

# Model Holder
model = None

def load_model_task():
    global model
    t_start = time.time()
    try:
        from faster_whisper import WhisperModel
        print(f"[PROFILER] Faster-Whisper Imported: {time.time() - original_start_time:.4f} (took {time.time() - t_start:.4f}s)")
        
        logger.info(f"Loading model from {MODEL_PATH}...")
        
        load_start = time.time()
        model = WhisperModel(
            MODEL_PATH, 
            device=DEVICE, 
            compute_type=COMPUTE_TYPE,
            local_files_only=True
        )
        print(f"[PROFILER] Model Loaded: {time.time() - original_start_time:.4f} (Load took {time.time() - load_start:.4f}s)")
        logger.info("Model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        sys.exit(1)

def audio_callback(indata, frames, time_info, status):
    if status:
        logger.warning(status)
    audio_queue.put(indata.copy())

def record_audio_task():
    t_start = time.time()
    import sounddevice as sd
    print(f"[PROFILER] SoundDevice Imported: {time.time() - original_start_time:.4f} (took {time.time() - t_start:.4f}s)")
    
    # Show Recording Notification
    try:
        speed_factor = config.get("speed_factor", 1.0)
        use_local = config.get("use_local_model", True)
        model_mode = "Local" if use_local else "API"
        model_name = os.path.basename(config.get("local_model_size", "unknown")) if use_local else "Groq"
        
        # Determine Memory Optimization Mode
        mem_mode = "Zero"
        if config.get("local_always_loaded"):
            mem_mode = "Persist"
        elif config.get("local_ram_cache"):
            mem_mode = "CPU"
            
        msg = f"Mode: {model_mode} | Model: {model_name}\nSpeed: {speed_factor}x | Mem: {mem_mode}"
        
        # 環境変数からnotification IDを取得（デーモンが設定）
        replaces_id = os.environ.get("STT_NOTIFICATION_ID")
        new_id = platform_utils.notify("🎙️ Recording", msg, replaces_id=replaces_id, timeout=0)  # 0 = 消えない
        
        # 新しいIDを環境変数に保存（次回用）
        if new_id:
            os.environ["STT_NOTIFICATION_ID"] = new_id
    except Exception as e:
        logger.warning(f"Could not show notification: {e}")

    logger.info("Starting recording...")
    
    device_id = config.get("device_index")
    if device_id == "default": device_id = None
    
    samplerate = 16000 
    
    try:
        sd_start = time.time()
        with sd.InputStream(samplerate=samplerate, device=device_id, channels=1, callback=audio_callback):
            print(f"[PROFILER] Recording STARTED: {time.time() - original_start_time:.4f} (SD Init took {time.time() - sd_start:.4f}s)")
            while not stop_event.is_set():
                time.sleep(0.1)
    except Exception as e:
        logger.error(f"Recording error: {e}")
        
    # Show Processing Notification (上書き)
    try:
        replaces_id = os.environ.get("STT_NOTIFICATION_ID")
        new_id = platform_utils.notify("⏳ Processing", "Transcribing...", replaces_id=replaces_id, timeout=2000)  # 2秒
        if new_id:
            os.environ["STT_NOTIFICATION_ID"] = new_id
    except: pass

        
    logger.info("Recording stopped.")
    recording_finished_event.set()

def type_text(text):
    import platform
    if not text: return
    
    logger.info(f"Typing: {text}")
    
    # Clipboard handling
    try:
        import pyperclip
        old_clipboard = pyperclip.paste()
        pyperclip.copy(text)
    except Exception:
        old_clipboard = ""

    # Typing
    try:
        from pynput.keyboard import Controller, Key
        keyboard = Controller()
        
        # Linux specific paste (Ctrl+V) is usually faster/safer than typing chars for Japanese
        keyboard.press(Key.ctrl)
        keyboard.press('v')
        keyboard.release('v')
        keyboard.release(Key.ctrl)
        
        # Restore clipboard if config enabled
        if config.get("clipboard_restore", False):
            time.sleep(0.5) # Wait for paste to finish
            pyperclip.copy(old_clipboard)
            
    except Exception as e:
        logger.error(f"Typing failed: {e}")


def main():
    # Start loading model in background
    loader_thread = threading.Thread(target=load_model_task, daemon=True)
    loader_thread.start()
    
    # Start recording in background
    recorder_thread = threading.Thread(target=record_audio_task, daemon=True)
    recorder_thread.start()
    
    # Handle Stop Signal (SIGINT from Daemon)
    def signal_handler(sig, frame):
        logger.info("Stop signal received. Processing...")
        stop_event.set()
        
    signal.signal(signal.SIGINT, signal_handler)
    
    # Main loop: wait for recording to finish (triggered by signal)
    # We loop here to keep main thread alive.
    while not recording_finished_event.is_set():
        time.sleep(0.05)
        
    # Recording finished. Process audio.
    logger.info("Processing audio...")
    
    # Collect all audio chunks
    audio_data = []
    while not audio_queue.empty():
        audio_data.append(audio_queue.get())
        
    if not audio_data:
        logger.warning("No audio recorded.")
        return

    # Concatenate and normalize
    audio_np = np.concatenate(audio_data, axis=0).flatten().astype(np.float32)
    
    # Wait for model load if not done
    loader_thread.join()
    
    if model:
        # Process Audio (Speed Up)
        speed_factor = config.get("speed_factor", 1.0)
        if speed_factor > 1.0:
            logger.info(f"Applying speed factor: {speed_factor}x")
            # Naive resampling (works for speed up)
            # New length = Old length / speed
            original_len = len(audio_np)
            new_len = int(original_len / speed_factor)
            
            # indices for interpolation
            indices = np.linspace(0, original_len - 1, new_len)
            
            audio_np = np.interp(indices, np.arange(original_len), audio_np).astype(np.float32)

        # Transcribe
        logger.info("Transcribing...")
        # VAD filter is good, verify standard args
        segments, info = model.transcribe(audio_np, beam_size=5, language="ja", vad_filter=True)
        
        full_text = "".join([segment.text for segment in segments]).strip()
        print(f"OUTPUT: {full_text}") # For debug/daemon logs
        
        if full_text:
            type_text(full_text)
    else:
        logger.error("Model did not load.")

if __name__ == "__main__":
    main()
