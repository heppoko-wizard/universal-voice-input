#!/usr/bin/env python3
"""
STT Daemon - pystray Edition (Cross-Platform)
ホットキーを監視し、Unified Workerを制御する。
pystrayでシステムトレイに常駐するクロスプラットフォーム実装。
"""
import sys
import os
import time
import subprocess
import threading
import signal
import socket
from pynput import keyboard
import config_manager
import platform_utils
import logging

log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [DAEMON] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "stt_daemon.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Daemon")

def check_singleton():
    """Ensure only one instance runs using a local TCP port."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", 34291))
        # Keep socket open to hold the lock
        return sock 
    except socket.error:
        print("Another instance is already running. Exiting.")
        sys.exit(1)

# pystray imports
import pystray
from PIL import Image

# --- Configuration ---
WORKER_SCRIPT = "stt_worker_unified.py"
OVERLAY_SCRIPT = "status_overlay.py"
PYTHON_CMD = sys.executable
ICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stt_icon.png")

class OverlayManager:
    def __init__(self):
        self.process = None
        self.lock = threading.Lock()
        
    def ensure_running(self):
        with self.lock:
            if self.process is None or self.process.poll() is not None:
                self._spawn()
    
    def _spawn(self):
        try:
            logger.info("Spawning overlay...")
            self.process = subprocess.Popen(
                [PYTHON_CMD, OVERLAY_SCRIPT],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
        except Exception as e:
            logger.info(f"Failed to spawn overlay: {e}")
            self.process = None

    def send_command(self, cmd):
        self.ensure_running()
        with self.lock:
            if self.process:
                try:
                    self.process.stdin.write(cmd + "\n")
                    self.process.stdin.flush()
                except:
                    self.process = None
                    
    def cleanup(self):
        with self.lock:
            if self.process:
                try:
                    self.process.stdin.write("QUIT\n")
                    self.process.stdin.flush()
                    self.process.wait(timeout=1)
                except:
                    self.process.terminate()
                self.process = None

class WorkerManager:
    def __init__(self, status_callback=None):
        self.process = None
        self.lock = threading.Lock()
        self.status_callback = status_callback
        self.monitor_thread = None
        
    def ensure_running(self):
        with self.lock:
            if self.process is None or self.process.poll() is not None:
                self._spawn()
                
    def restart(self):
        self.cleanup()
        self.ensure_running()

    def _spawn(self):
        try:
            logger.info("Spawning worker...")
            self.process = subprocess.Popen(
                [PYTHON_CMD, WORKER_SCRIPT],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            self.monitor_thread = threading.Thread(target=self._monitor_output, daemon=True)
            self.monitor_thread.start()
            
        except Exception as e:
            logger.info(f"Failed to spawn worker: {e}")
            self.process = None

    def _monitor_output(self):
        if not self.process: return
        
        try:
            for line in iter(self.process.stdout.readline, ''):
                if not line: break
                line = line.strip()
                logger.info(f"[WORKER] {line}")
                
                if line.startswith("[STATUS]"):
                    status = line.replace("[STATUS]", "").strip()
                    if self.status_callback:
                        self.status_callback(status)
        except Exception as e:
            logger.info(f"Monitor error: {e}")
        
        # ワーカープロセス終了時: 録音状態を確実にリセット
        logger.info("[WORKER] Process exited. Resetting state.")
        if self.status_callback:
            self.status_callback("READY")

    def send_command(self, cmd):
        self.ensure_running()
        with self.lock:
            if self.process and self.process.poll() is None:
                try:
                    self.process.stdin.write(cmd + "\n")
                    self.process.stdin.flush()
                except BrokenPipeError:
                    logger.info("Worker pipe broken. Restarting...")
                    self.process = None
                    self._spawn()
                    if self.process:
                        self.process.stdin.write(cmd + "\n")
                        self.process.stdin.flush()

    def cleanup(self):
        with self.lock:
            if self.process:
                try:
                    self.process.stdin.write("QUIT\n")
                    self.process.stdin.flush()
                    self.process.wait(timeout=2)
                except:
                    self.process.terminate()
                self.process = None

class STTDaemon:
    def __init__(self):
        self.config = config_manager.load_config()
        self.hotkey = self.config.get("hotkey", "<ctrl>+<shift>+<space>")
        
        self.overlay_mgr = OverlayManager()
        self.worker_mgr = WorkerManager(status_callback=self.on_worker_status)
        
        self.recording = False
        self.listener = None
        
        self.icon = pystray.Icon("stt-daemon")
        self.icon.title = "STT Daemon"
        try:
            self.icon.icon = Image.open(ICON_PATH)
        except Exception as e:
            logger.error(f"Failed to load icon: {e}")
            self.icon.icon = Image.new('RGB', (64, 64), color='black')
        
        # メニュー作成
        self.rebuild_menu()
        
        # プリロード
        self.overlay_mgr.ensure_running()
        self.worker_mgr.ensure_running()
        
        # 起動時マイクチェック（バックグラウンド）
        threading.Thread(target=self._startup_mic_check, daemon=True).start()
        
        logger.info(f"--- STT Daemon (pystray) ---")
        
    def rebuild_menu(self):
        """設定言語に基づいてメニューを再構築"""
        import i18n
        lang = self.config.get("ui_language", "ja")
        
        menu_items = [
            pystray.MenuItem(i18n.get_text("tray_settings", lang), self.on_settings),
            pystray.MenuItem(i18n.get_text("tray_exit", lang), self.on_exit)
        ]
        self.icon.menu = pystray.Menu(*menu_items)
        
        # ホットキー設定
        self.hotkey_mode = self.config.get("hotkey_mode", "toggle")
        self.setup_hotkey()
        
    def on_worker_status(self, status):
        self.overlay_mgr.send_command(status)
        # ワーカーがREADYに戻った場合、デーモン側の状態もリセット
        # （録音エラー時のデッドロック防止）
        if status == "READY":
            self.recording = False
        elif status == "UNLOADED":
            # モデルアンロード完了 → オーバーレイをクリア
            self.recording = False
            self.overlay_mgr.send_command("READY")
        elif status == "MODEL_ERROR":
            self.recording = False
            self.overlay_mgr.send_command("READY")
            import i18n
            lang = self.config.get("ui_language", "ja")
            self._send_notification(
                "STT - Model Error",
                i18n.get_text("model_load_error", lang),
                "critical"
            )
        elif status == "DEVICE_ERROR":
            self.recording = False
            self.overlay_mgr.send_command("READY")
            self._send_notification(
                "STT - Device Error",
                "マイクデバイスにアクセスできませんでした。\nUSBを挿し直すか、設定を確認してください。",
                "critical"
            )
        elif status == "SILENT_ERROR":
            self.recording = False
            self.overlay_mgr.send_command("READY")
            self._send_notification(
                "STT - Mic Warning",
                "マイクが音を拾っていません。\nミュートになっていないか、接続を確認してください。",
                "normal"
            )

    def _startup_mic_check(self):
        """起動時のマイクチェック（警告のみ、config書き換えなし）"""
        import i18n
        try:
            import mic_checker
        except ImportError:
            logger.info("mic_checker module not found, skipping mic check")
            return
        
        device_idx = self.config.get("device_index")
        sample_rate = self.config.get("sample_rate", 44100)
        
        logger.info(f"Mic check: device = {device_idx}")
        result = mic_checker.check_device(device_idx, sample_rate=sample_rate)
        
        if result["error"]:
            # デバイスを開けなかった
            msg = f"マイク ({result['device_name']}) にアクセスできません: {result['error']}"
            logger.info(f"Mic check: WARNING - {msg}")
            self._send_notification("STT - Mic Check", msg, "warning")
        elif result["silent"]:
            # 完全無音
            msg = f"マイク ({result['device_name']}) が無音です。接続を確認してください。"
            logger.info(f"Mic check: WARNING - {msg}")
            self._send_notification("STT - Mic Check", msg, "warning")
        else:
            logger.info(f"Mic check: OK - {result['device_name']} (RMS={result['rms']:.6f})")
    
    def _send_notification(self, title, message, urgency="normal"):
        """デスクトップ通知を送信（pystray機能を使用）"""
        try:
            self.icon.notify(message, title=title)
        except Exception as e:
            logger.info(f"Notification error: {e}")

    def on_activate(self):
        """Toggle mode の動作"""
        if self.recording:
            logger.info("Hotkey: STOP (Toggle)")
            self.worker_mgr.send_command("STOP")
            self.recording = False
        else:
            logger.info("Hotkey: START (Toggle)")
            self.worker_mgr.send_command("START")
            self.recording = True

    def on_press_hold(self):
        """Hold mode の開始動作"""
        if not self.recording:
            logger.info("Hotkey: START (Hold)")
            self.worker_mgr.send_command("START")
            self.recording = True

    def on_release_hold(self):
        """Hold mode の終了動作"""
        if self.recording:
            logger.info("Hotkey: STOP (Hold)")
            self.worker_mgr.send_command("STOP")
            self.recording = False

    def setup_hotkey(self):
        try:
            # 古いリスナーがあれば安全に停止（二重起動防止）
            if getattr(self, "listener", None):
                try:
                    self.listener.stop()
                except Exception as e:
                    logger.warning(f"Failed to stop previous hotkey listener: {e}")
            
            # pynputのHotKeyオブジェクトを作成
            hotkey_str = self.hotkey
            # pynput.keyboard.HotKey.parse を通して構造化
            keys = keyboard.HotKey.parse(hotkey_str)
            
            def _on_activate_wrapped():
                if self.hotkey_mode == "hold":
                    self.on_press_hold()
                else:
                    self.on_activate()

            self.hotkey_obj = keyboard.HotKey(keys, _on_activate_wrapped)
            
            def on_press(key):
                self.hotkey_obj.press(self.listener.canonical(key))
            
            def on_release(key):
                # ホールドモードの場合、ホットキーのどれか1つでも離されたらSTOP
                if self.hotkey_mode == "hold" and self.recording:
                    # 離されたキーがホットキーの一部かどうか判定し、録音中なら止める
                    # HotKey.release自体は全キー離されるまで発火しないので、独自に判定
                    canonical_key = self.listener.canonical(key)
                    if canonical_key in keys:
                        self.on_release_hold()
                
                self.hotkey_obj.release(self.listener.canonical(key))

            self.listener = keyboard.Listener(on_press=on_press, on_release=on_release)
            self.listener.start()
            
            logger.info(f"Hotkey Listener Started: {self.hotkey} (Mode: {self.hotkey_mode})")
            self.overlay_mgr.send_command("READY")
        except Exception as e:
            logger.info(f"Hotkey Error: {e}")

    def reload_config(self):
        logger.info("Reloading configuration...")
        try:
            self.config = config_manager.load_config()
            new_hotkey = self.config.get("hotkey", "<ctrl>+<shift>+<space>")
            new_mode = self.config.get("hotkey_mode", "toggle")
            
            if new_hotkey != self.hotkey or new_mode != self.hotkey_mode:
                logger.info(f"Hotkey updated: {self.hotkey}({self.hotkey_mode}) -> {new_hotkey}({new_mode})")
                self.hotkey = new_hotkey
                self.hotkey_mode = new_mode
                if self.listener:
                    self.listener.stop()
                self.setup_hotkey()

            self.worker_mgr.restart()
            self.overlay_mgr.cleanup()
            self.overlay_mgr.ensure_running()
            
            # メニューを再構築
            self.rebuild_menu()
            self.icon.update_menu()
            
        except Exception as e:
            logger.info(f"Reload failed: {e}")

    def on_settings(self, icon, item):
        def _run():
            logger.info("Opening GUI...")
            try:
                subprocess.run([PYTHON_CMD, "gui.py"], cwd=os.path.dirname(os.path.abspath(__file__)))
                logger.info("GUI closed.")
                self.reload_config()
            except Exception as e:
                logger.info(f"GUI Error: {e}")
        threading.Thread(target=_run, daemon=True).start()

    def on_exit(self, icon, item):
        logger.info("Exiting...")
        if self.listener:
            self.listener.stop()
        self.worker_mgr.cleanup()
        self.overlay_mgr.cleanup()
        self.icon.stop()

    def run(self):
        # シグナルハンドラ設定
        def _handle_signal(sig, frame):
            logger.info(f"Received signal {sig}")
            if hasattr(signal, "SIGUSR1") and sig == signal.SIGUSR1:
                self.reload_config()
            else:
                self.on_exit(None, None)

        if hasattr(signal, "SIGUSR1"):
            signal.signal(signal.SIGUSR1, _handle_signal)
        signal.signal(signal.SIGINT, _handle_signal)
        signal.signal(signal.SIGTERM, _handle_signal)
        
        self.icon.run()

if __name__ == "__main__":
    # Prevent double execution
    lock_socket = check_singleton()
    
    app = STTDaemon()
    app.run()
