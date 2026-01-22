#!/usr/bin/env python3
"""
STT Worker Unified
録音、推論、常駐管理をひとつに統合したワーカー
オーバーレイ対応版：通知機能削除、ステータス出力追加
"""
import os
import sys
import time
import signal
import threading
import queue
import logging
import select
import numpy as np
import sounddevice as sd
import config_manager
import platform_utils

import gc

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [WORKER] %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger("UnifiedWorker")

# 初期メモリ使用量ログ
try:
    import resource
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    logger.info(f"Initial Memory Usage: {usage / 1024:.2f} MB")
except ImportError:
    logger.info("resource module not available. Memory logging disabled.")

def get_current_memory_usage_mb():
    """現在のRSS（物理メモリ使用量）をMBで返す"""
    try:
        with open("/proc/self/status", "r") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1024
    except:
        pass
    return 0.0

def log_memory_usage(label=""):
    """メモリ使用量をログに出力 (RSSとPeakの両方)"""
    try:
        rss = get_current_memory_usage_mb()
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        logger.info(f"Memory Usage [{label}]: RSS={rss:.2f} MB, Peak={peak:.2f} MB")
    except:
        pass

# --- Constants ---
SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_SIZE = 1024

class UnifiedSTTWorker:
    def __init__(self):
        self.config = config_manager.load_config()
        self.model_path = self.config.get("local_model_size", "models/kotoba-whisper-v2.2-int8")
        self.device = self.config.get("local_device", "cuda")
        self.compute_type = self.config.get("local_compute_type", "int8")
        self.timeout = self.config.get("hybrid_timeout", 300)
        
        self.model = None
        self.model_loading = False
        self.model_ready_event = threading.Event()
        
        self.audio_queue = queue.Queue()
        self.recording = False
        self.stop_recording_event = threading.Event()
        self.recording_thread = None
        
        # 処理キューの追加 (録音と処理の切り離し)
        self.transcription_queue = queue.Queue()
        
        self.last_activity = time.time()
        
        # 設定: モデル保持時間 (秒)
        # -1: 常時保持 (Always Loaded)
        # 0: 即時解放 (Zero Memory)
        # >0: 指定時間保持 (Hybrid)
        self.model_timeout = self.config.get("local_model_timeout", -1)
        logger.info(f"Model timeout config: {self.model_timeout}")
        
        # 常時保持モード(-1)の場合は初期ロード
        if self.model_timeout == -1:
            self.load_model(initial=True)
        else:
            # それ以外（On-demand / Hybrid）は必要時ロード
            logger.info("On-demand/Hybrid mode: Model will be loaded upon recording.")
            # READYシグナルを出して待機
            print("[STATUS] READY")
            sys.stdout.flush()

        # タイムアウト監視スレッドの開始
        threading.Thread(target=self._monitor_timeout, daemon=True).start()
        
        # バックグラウンド処理スレッドの開始
        threading.Thread(target=self._transcription_worker, daemon=True).start()

    def _monitor_timeout(self):
        """モデル保持時間が指定されている場合、アイドル時間を監視してアンロード"""
        while True:
            time.sleep(1)
            if self.model and self.model_timeout > 0:
                # 録音中や、処理待ちがある間はアンロードしない
                if not self.recording and not self.model_loading and self.transcription_queue.empty():
                    elapsed = time.time() - self.last_activity
                    if elapsed > self.model_timeout:
                        logger.info(f"Timeout reached ({elapsed:.1f}s > {self.model_timeout}s). Unloading model...")
                        self.unload_model()

    def unload_model(self):
        if self.model:
            log_memory_usage("Before Unload")
            logger.info("Unloading model contents...")
            
            # ctranslate2の内部キャッシュをクリア（もしあれば）
            try:
                import ctranslate2
                ctranslate2.set_realloc_threshold(0) # 即時解放を促す
            except:
                pass

            # モデルの削除
            self.model = None
            self.model_ready_event.clear()
            
            # GCを徹底
            for _ in range(3):
                gc.collect()
            
            log_memory_usage("After Unload")
            print("[STATUS] UNLOADED")
            sys.stdout.flush()
            
            # プロセスを終了してOSにメモリを完全に返却する
            # デーモン側がプロセスの死を検知して次回のSTART時に再起動する
            logger.info("Exiting worker process to ensure complete memory cleanup.")
            time.sleep(0.5) # stdoutのフラッシュ時間を確保
            import os
            os._exit(0)

    def load_model(self, initial=False):
        if self.model is not None or self.model_loading:
            return

        def _load():
            try:
                self.model_loading = True
                log_memory_usage("Before Load")
                logger.info(f"Loading model: {os.path.basename(self.model_path)}")
                
                from faster_whisper import WhisperModel
                self.model = WhisperModel(
                    self.model_path,
                    device=self.device,
                    compute_type=self.compute_type,
                    local_files_only=True
                )
                logger.info("Model loaded successfully.")
                log_memory_usage("After Load")
                self.model_ready_event.set()
                
                if initial:
                    print("[STATUS] READY")
                    sys.stdout.flush()
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
            finally:
                self.model_loading = False

        threading.Thread(target=_load, daemon=True).start()

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            logger.warning(f"Audio status: {status}")
        self.audio_queue.put(indata.copy())

    def start_recording(self):
        if self.recording:
            return
        
        # 毎回最新の設定を読み込む
        self.config = config_manager.load_config()
        
        self.recording = True
        self.stop_recording_event.clear()

        # ローカルモードかつモデルがない場合はロード開始（バックグラウンド）
        use_local = self.config.get("use_local_model", True)
        if use_local and self.model is None:
            self.load_model(initial=False)
        elif not use_local and self.model is not None:
            # オンラインモードに切り替わった場合、ローカルモデルをアンロード
            logger.info("Switched to online mode, unloading local model...")
            self.unload_model()
        
        # STATUS: RECORDING
        print("[STATUS] REC")
        sys.stdout.flush()
        
        with self.audio_queue.mutex:
            self.audio_queue.queue.clear()
            
        def _record_loop():
            device_idx = self.config.get("device_index")
            if device_idx == "default": device_idx = None
            
            try:
                with sd.InputStream(samplerate=SAMPLE_RATE, device=device_idx, channels=CHANNELS, callback=self._audio_callback):
                    logger.info("Recording STARTED")
                    while not self.stop_recording_event.is_set():
                        time.sleep(0.05)
            except Exception as e:
                logger.error(f"Recording error: {e}")
                self.recording = False
        
        self.recording_thread = threading.Thread(target=_record_loop, daemon=True)
        self.recording_thread.start()

    def stop_and_transcribe(self):
        if not self.recording:
            return

        # 停止シグナル
        self.stop_recording_event.set()
        if self.recording_thread:
            self.recording_thread.join(timeout=2.0)
        self.recording = False
        logger.info("Recording STOPPED")

        # 設定読み込み
        self.config = config_manager.load_config()
        use_local = self.config.get("use_local_model", True)
        speed_factor = self.config.get("speed_factor", 1.0)

        # データを回収
        audio_data = []
        while not self.audio_queue.empty():
            audio_data.append(self.audio_queue.get())
            
        if not audio_data:
            logger.warning("No audio data recorded.")
            print("[STATUS] READY")
            sys.stdout.flush()
            return

        # 前処理 (データをキューへ)
        audio_np = np.concatenate(audio_data, axis=0).flatten().astype(np.float32)
        if speed_factor > 1.0:
            indices = np.arange(0, len(audio_np), speed_factor)
            audio_np = audio_np[indices.astype(int)]

        # キューにタスクを投入
        task = {
            "audio": audio_np,
            "use_local": use_local,
            "config": self.config
        }
        self.transcription_queue.put(task)
        logger.info("Enqueued transcription task.")

        # 即座にREADYを返す (次の録音を可能にする)
        print("[STATUS] READY")
        sys.stdout.flush()

    def _transcription_worker(self):
        """バックグラウンドでキューを監視して文字起こしを行う"""
        while True:
            try:
                task = self.transcription_queue.get()
                if task is None: break # 終了用
                
                audio_np = task["audio"]
                use_local = task["use_local"]
                config = task["config"]
                
                self.process_task(audio_np, use_local, config)
                self.transcription_queue.task_done()
                
                # アクティビティ更新 (モデルアンロードの起点を処理終了時にする)
                self.last_activity = time.time()
                
                # アンロード判定 (0秒設定、またはタイムアウトチェックのためにキューが空になったことをトリガーにする)
                self.model_timeout = config.get("local_model_timeout", -1)
                if use_local and self.model_timeout == 0 and not self.recording and self.transcription_queue.empty():
                    self.unload_model()
                
            except Exception as e:
                logger.error(f"Worker thread error: {e}")
                time.sleep(1)

    def process_task(self, audio_np, use_local, config):
        """実際の文字起こし処理"""
        if use_local:
            # ローカルモデルで処理
            if not self.model_ready_event.is_set():
                logger.info("Waiting for model to load...")
                if not self.model_ready_event.wait(timeout=30):
                    logger.error("Model load timed out.")
                    return

            if self.model:
                start_time = time.time()
                segments, _ = self.model.transcribe(audio_np, beam_size=5, language="ja", vad_filter=True)
                text_list = []
                for s in segments:
                    text_list.append(s.text)
                text = "".join(text_list).strip()
                
                del segments
                del text_list
                
                logger.info(f"Transcribed (Local, {time.time() - start_time:.2f}s): {text}")
                if text:
                    platform_utils.type_text(text)
            else:
                logger.error("Model is None.")
                
        else:
            # オンラインAPI（Groq）で処理
            try:
                import io
                import wave
                from groq import Groq
                
                wav_buffer = io.BytesIO()
                with wave.open(wav_buffer, 'wb') as wav_file:
                    wav_file.setnchannels(CHANNELS)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(SAMPLE_RATE)
                    audio_int16 = (audio_np * 32767).astype(np.int16)
                    wav_file.writeframes(audio_int16.tobytes())
                
                wav_buffer.seek(0)
                wav_buffer.name = "audio.wav"
                
                api_key = config.get("api_keys", {}).get("groq", "")
                if not api_key:
                    logger.error("Groq API key not found")
                    return
                
                client = Groq(api_key=api_key)
                model_id = config.get("api_models", {}).get("groq", "whisper-large-v3-turbo")
                
                start_time = time.time()
                transcription = client.audio.transcriptions.create(
                    file=wav_buffer,
                    model=model_id,
                    language="ja"
                )
                text = transcription.text.strip()
                logger.info(f"Transcribed (Online, {time.time() - start_time:.2f}s): {text}")
                
                if text:
                    platform_utils.type_text(text)
                    
            except Exception as e:
                logger.error(f"Online API error: {e}")

    def run(self):
        logger.info("Interactive Loop Started")
        
        while True:
            # 録音中や、処理待ちのタスクがある間は終了しない
            if not self.recording and self.transcription_queue.empty() and (time.time() - self.last_activity > self.timeout):
                logger.info(f"Timeout ({self.timeout}s). Exiting.")
                break

            r, _, _ = select.select([sys.stdin], [], [], 0.1)
            if r:
                line = sys.stdin.readline()
                if not line: break 
                
                cmd = line.strip().upper()
                self.last_activity = time.time()
                
                if cmd == "START":
                    self.start_recording()
                    print("ACK:START")
                    sys.stdout.flush()
                elif cmd == "STOP":
                    self.stop_and_transcribe()
                    print("ACK:STOP")
                    sys.stdout.flush()
                elif cmd == "QUIT":
                    break
                elif cmd == "PING":
                    print("PONG")
                    sys.stdout.flush()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
    worker = UnifiedSTTWorker()
    worker.run()
