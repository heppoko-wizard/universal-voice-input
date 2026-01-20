#!/usr/bin/env python3
"""
STT Daemon - Hotkey監視 & Worker管理

4つのモードをサポート:
1. Zero Memory: 毎回ワーカーを起動して終了
2. CPU Cache: 旧方式（ほぼZeroと同じ）
3. Hybrid: 常駐ワーカーを使用、一定時間で自動終了
4. Persistent: 常駐ワーカーを使用、自動終了なし（core.pyと同等）
"""
import signal
import sys
import subprocess
import time
import threading
from pynput import keyboard
import config_manager
import os

# --- Daemon Configuration ---
WORKER_SCRIPT = "stt_worker.py"
WORKER_PERSISTENT_SCRIPT = "stt_worker_persistent.py"
PYTHON_CMD = sys.executable

class STTDaemon:
    def __init__(self):
        self.worker_process = None
        self.worker_ready_event = threading.Event()
        self.config = config_manager.load_config()
        self.hotkey_str = self.config.get("hotkey", "<ctrl>+<shift>+<space>")
        self.running = True
        self.recording = False
        self.notification_id = None  # 通知IDを保持
        
        # Determine mode
        self.hybrid_mode = self.config.get("hybrid_mode", False)
        self.persistent_mode = self.config.get("local_always_loaded", False)
        
        if self.persistent_mode:
            self.mode = "persistent"
        elif self.hybrid_mode:
            self.mode = "hybrid"
        else:
            self.mode = "zero"
        
        print(f"--- STT Daemon Started ---")
        print(f"Mode: {self.mode}")
        print(f"Hotkey: {self.hotkey_str}")
        
        # Preload for Hybrid/Persistent modes
        if self.mode in ["hybrid", "persistent"]:
            print("Preloading worker in background...")
            self._spawn_persistent_worker()
            
        print("Ready. Press hotkey to Speak.")

    def _spawn_persistent_worker(self):
        """ワーカープロセスを起動（バックグラウンド）"""
        try:
            self.worker_ready_event.clear()
            self.worker_process = subprocess.Popen(
                [PYTHON_CMD, WORKER_PERSISTENT_SCRIPT],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            # 監視スレッド開始
            monitor_thread = threading.Thread(target=self._monitor_worker_output, daemon=True)
            monitor_thread.start()
        except Exception as e:
            print(f"Failed to start persistent worker: {e}")
            self.worker_process = None

    def on_hotkey(self):
        """ホットキーが押された時の処理"""
        if self.mode in ["hybrid", "persistent"]:
            self._handle_persistent_mode()
        else:
            self._handle_oneshot_mode()
    
    def _handle_oneshot_mode(self):
        """Zero/CPUモード: 毎回ワーカーを起動・終了"""
        if self.worker_process and self.worker_process.poll() is None:
            # Worker is running -> STOP recording
            print("Hotkey pressed: Stopping recording...")
            self.worker_process.send_signal(signal.SIGINT)
        else:
            # Worker is dead or None -> START recording
            print("Hotkey pressed: Starting worker...")
            try:
                # 環境変数を準備
                env = os.environ.copy()
                if self.notification_id:
                    env["STT_NOTIFICATION_ID"] = self.notification_id
                
                self.worker_process = subprocess.Popen(
                    [PYTHON_CMD, WORKER_SCRIPT],
                    cwd=os.path.dirname(os.path.abspath(__file__)),
                    env=env
                )
            except Exception as e:
                print(f"Failed to start worker: {e}")
    
    def _handle_persistent_mode(self):
        """Hybrid/Persistentモード: 常駐ワーカーにコマンドを送信"""
        # ワーカーが起動していなければ起動
        if self.worker_process is None or self.worker_process.poll() is not None:
            print("Starting persistent worker...")
            self._spawn_persistent_worker()
            # ワーカーの準備完了を待つ (最大30秒)
            if not self._wait_for_worker_ready():
                # 失敗したらクリーンアップ
                if self.worker_process:
                    self.worker_process.terminate()
                    self.worker_process = None
                return
            self.recording = False
        
        # まだ準備完了していない場合（プリロード中など）
        if not self.worker_ready_event.is_set():
             print("Worker is loading... Waiting.")
             if not self._wait_for_worker_ready():
                 return

        # 録音トグル
        if self.recording:
            print("Sending STOP command...")
            self._send_command("STOP")
            self.recording = False
        else:
            print("Sending START command...")
            self._send_command("START")
            self.recording = True
    
    def _send_command(self, cmd):
        """ワーカーにコマンドを送信"""
        if self.worker_process and self.worker_process.poll() is None:
            try:
                self.worker_process.stdin.write(cmd + "\n")
                self.worker_process.stdin.flush()
            except Exception as e:
                print(f"Failed to send command: {e}")
    
    def _wait_for_worker_ready(self):
        """ワーカーの準備完了Eventを待つ"""
        print("Waiting for worker to be ready...")
        if self.worker_ready_event.wait(timeout=30):
            print("Worker is ready!")
            return True
        else:
            print("Worker ready timeout.")
            return False
    
    def _monitor_worker_output(self):
        """ワーカーの出力を監視するスレッド。全てのstdout読み込みはここで行う。"""
        while self.running and self.worker_process and self.worker_process.poll() is None:
            try:
                # readlineはブロッキングする可能性があるので、selectを使うか、
                # あるいは daemon=True なので単純にループで良いが、
                # プロセス終了検知のため readline() が空文字を返したらループを抜ける
                line = self.worker_process.stdout.readline()
                if not line:
                    break
                
                line = line.strip()
                if line:
                    print(f"[WORKER] {line}")
                    if "Ready" in line:
                         self.worker_ready_event.set()
            except Exception as e:
                print(f"Monitor error: {e}")
                break
        
        if self.worker_process:
            print("Worker process output stream ended.")
    
    def run(self):
        # Setup Hotkey Listener
        try:
            with keyboard.GlobalHotKeys({
                self.hotkey_str: self.on_hotkey
            }) as h:
                while self.running:
                    time.sleep(1)
        except Exception as e:
            print(f"Hotkey Error: {e}")
    
    def cleanup(self):
        """終了処理"""
        if self.worker_process and self.worker_process.poll() is None:
            print("Stopping worker...")
            try:
                self._send_command("QUIT")
                self.worker_process.wait(timeout=5)
            except:
                self.worker_process.terminate()

if __name__ == "__main__":
    daemon = STTDaemon()
    try:
        daemon.run()
    except KeyboardInterrupt:
        print("\nDaemon stopping...")
    finally:
        daemon.cleanup()
