#!/usr/bin/env python3
"""
STT Worker - Persistent Mode (Hybrid)

このスクリプトは、Hybridモード用の常駐ワーカーです。
- デーモンからの「START」コマンドで録音開始
- 「STOP」コマンドで録音停止＆文字起こし
- 一定時間コマンドがなければ自動終了（VRAMを完全に解放）
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
import select
import subprocess
import platform_utils

print(f"[PROFILER] Basic Imports Done: {time.time() - original_start_time:.4f}")

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("stt_worker_persistent")

# Configuration
config = config_manager.load_config()
print(f"[PROFILER] Config Loaded: {time.time() - original_start_time:.4f}")

MODEL_PATH = config.get("local_model_size", "models/kotoba-whisper-v2.2-int8")
DEVICE = config.get("local_device", "cuda")
COMPUTE_TYPE = config.get("local_compute_type", "int8")
HYBRID_TIMEOUT = config.get("hybrid_timeout", 300)

# Global State
model = None
audio_queue = queue.Queue()
stop_recording_event = threading.Event()
recording_thread = None
model_load_thread = None # For background loading
active_notification_id = None

def load_model_task():
    """モデルをロードしてVRAMに常駐させる（バックグラウンド実行用）"""
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

def start_recording():
    """録音を開始する（別スレッド）"""
    global recording_thread
    stop_recording_event.clear()
    
    # 既存の録音データをクリア
    while not audio_queue.empty():
        audio_queue.get()
    
    def _record():
        device_id = config.get("device_index")
        if device_id == "default": device_id = None
        samplerate = 16000
        
        # Show Notification
        try:
            speed_factor = config.get("speed_factor", 1.0)
            model_name = os.path.basename(MODEL_PATH)
            loader_status = "Ready" if model else "Loading..."
            msg = f"Mode: Hybrid | Model: {model_name}\nSpeed: {speed_factor}x | {loader_status}"

            if sys.platform == "linux":
                # platform_utils を使用して上書き
                global active_notification_id
                active_notification_id = platform_utils.notify("🎙️ Recording", msg, replaces_id=active_notification_id, timeout=0)  # 0 = 消えない
            else:
                from plyer import notification
                # Suppress dbus warning
                import warnings
                warnings.filterwarnings("ignore", category=UserWarning, module="plyer")
                notification.notify(title="🎙️ Recording", message=msg, timeout=3)
        except Exception as e:
            logger.warning(f"Notification error: {e}")
        
        try:
            with sd.InputStream(samplerate=samplerate, device=device_id, channels=1, callback=audio_callback):
                print(f"[WORKER] Recording STARTED")
                while not stop_recording_event.is_set():
                    time.sleep(0.05)
        except Exception as e:
            logger.error(f"Recording error: {e}")
        
        print(f"[WORKER] Recording STOPPED")
    
    recording_thread = threading.Thread(target=_record, daemon=True)
    recording_thread.start()

def stop_recording_and_transcribe():
    """録音を停止し、文字起こしを行う"""
    stop_recording_event.set()
    
    if recording_thread:
        recording_thread.join(timeout=2.0)
    
    # Collect audio
    audio_data = []
    while not audio_queue.empty():
        audio_data.append(audio_queue.get())
    
    if not audio_data:
        logger.warning("No audio recorded.")
        return
    
    audio_np = np.concatenate(audio_data, axis=0).flatten().astype(np.float32)
    
    # Speed Up
    speed_factor = config.get("speed_factor", 1.0)
    if speed_factor > 1.0:
        original_len = len(audio_np)
        new_len = int(original_len / speed_factor)
        indices = np.linspace(0, original_len - 1, new_len)
        audio_np = np.interp(indices, np.arange(original_len), audio_np).astype(np.float32)
    
    # Wait for model load
    if model_load_thread and model_load_thread.is_alive():
        logger.info("Waiting for model load to complete...")
        try:
            if sys.platform == "linux":
                global active_notification_id
                active_notification_id = platform_utils.notify("⏳ Loading Model...", "Please wait...", replaces_id=active_notification_id, timeout=2000)  # 2秒
            else:
                from plyer import notification
                notification.notify(title="⏳ Loading Model...", message="Please wait...", timeout=2)
        except: pass
        model_load_thread.join()
        
    if not model:
        logger.error("Model failed to load.")
        return

    # Transcribe
    logger.info("Transcribing...")
    try:
        if sys.platform == "linux":
            global active_notification_id
            active_notification_id = platform_utils.notify("⏳ Processing", "Transcribing...", replaces_id=active_notification_id, timeout=2000)  # 2秒
        else:
            from plyer import notification
            notification.notify(title="⏳ Processing", message="Transcribing...", timeout=2)
    except: pass
    
    segments, info = model.transcribe(audio_np, beam_size=5, language="ja", vad_filter=True)
    full_text = "".join([segment.text for segment in segments]).strip()
    print(f"OUTPUT: {full_text}")
    
    if full_text:
        type_text(full_text)

# ... type_text is checking ...

def main():
    """メインループ: stdinからコマンドを受け取る"""
    global model_load_thread
    
    # 初期ロード開始（バックグラウンド）
    model_load_thread = threading.Thread(target=load_model_task, daemon=True)
    model_load_thread.start()
    
    last_activity = time.time()
    recording = False
    
    print("[WORKER] Ready. Waiting for commands (START/STOP/QUIT)...")
    sys.stdout.flush()
    
    while True:
        # 自動消滅チェック
        if time.time() - last_activity > HYBRID_TIMEOUT:
            # 録音中は死なない
            if not recording:
                logger.info(f"Timeout ({HYBRID_TIMEOUT}s). Exiting to release VRAM.")
                break
        
        # stdin から非同期にコマンドを読む (0.5秒タイムアウト)
        # select を使ってブロッキングを回避
        if sys.stdin in select.select([sys.stdin], [], [], 0.5)[0]:
            line = sys.stdin.readline().strip().upper()
            if line:
                last_activity = time.time()
                
                if line == "START":
                    if not recording:
                        start_recording()
                        recording = True
                        print("[WORKER] ACK:START")
                        sys.stdout.flush()
                elif line == "STOP":
                    if recording:
                        stop_recording_and_transcribe()
                        recording = False
                        print("[WORKER] ACK:STOP")
                        sys.stdout.flush()
                elif line == "QUIT":
                    logger.info("QUIT command received.")
                    break
                elif line == "PING":
                    # Keep-alive check from daemon
                    print("[WORKER] PONG")
                    sys.stdout.flush()
    
    logger.info("Worker exiting.")
    sys.exit(0)

if __name__ == "__main__":
    main()
