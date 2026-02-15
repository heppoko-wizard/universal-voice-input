#!/usr/bin/env python3
"""
STT Daemon - AppIndicator Edition
ホットキーを監視し、Unified Workerを制御する。
AppIndicatorでシステムトレイに常駐（KDE/GNOME対応）
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

def check_singleton():
    """Ensure only one instance runs using an abstract socket."""
    # Abstract namespace socket (starts with null byte)
    # This is automatically cleaned up by OS when process dies
    socket_name = "\0stt_daemon_singleton_lock"
    
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.bind(socket_name)
        # Keep socket open to hold the lock
        return sock 
    except socket.error:
        print("Another instance is already running. Exiting.")
        sys.exit(1)

# AppIndicator imports
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk, AppIndicator3, GLib

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
            print("Spawning overlay...")
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
            print(f"Failed to spawn overlay: {e}")
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
            print("Spawning worker...")
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
            print(f"Failed to spawn worker: {e}")
            self.process = None

    def _monitor_output(self):
        if not self.process: return
        
        try:
            for line in iter(self.process.stdout.readline, ''):
                if not line: break
                line = line.strip()
                print(f"[WORKER] {line}")
                
                if line.startswith("[STATUS]"):
                    status = line.replace("[STATUS]", "").strip()
                    if self.status_callback:
                        self.status_callback(status)
        except Exception as e:
            print(f"Monitor error: {e}")
        
        # ワーカープロセス終了時: 録音状態を確実にリセット
        print("[WORKER] Process exited. Resetting state.")
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
                    print("Worker pipe broken. Restarting...")
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

class STTDaemonAppIndicator:
    def __init__(self):
        self.config = config_manager.load_config()
        self.hotkey = self.config.get("hotkey", "<ctrl>+<shift>+<space>")
        
        self.overlay_mgr = OverlayManager()
        self.worker_mgr = WorkerManager(status_callback=self.on_worker_status)
        
        self.recording = False
        self.listener = None
        
        # AppIndicator作成
        self.indicator = AppIndicator3.Indicator.new(
            "stt-daemon",
            ICON_PATH,
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        
        # メニュー作成
        self.rebuild_menu()
        
        # プリロード
        self.overlay_mgr.ensure_running()
        self.worker_mgr.ensure_running()
        
        # ホットキー設定
        self.setup_hotkey()
        
        # 起動時マイクチェック（無効化: device_indexを誤って上書きする問題があるため）
        # threading.Thread(target=self._startup_mic_check, daemon=True).start()
        
        print(f"--- STT Daemon (AppIndicator) ---")
        
    def rebuild_menu(self):
        """設定言語に基づいてメニューを再構築"""
        import i18n
        lang = self.config.get("ui_language", "ja")
        
        menu = Gtk.Menu()
        
        item_settings = Gtk.MenuItem(label=i18n.get_text("tray_settings", lang))
        item_settings.connect("activate", self.on_settings)
        menu.append(item_settings)
        
        item_quit = Gtk.MenuItem(label=i18n.get_text("tray_exit", lang))
        item_quit.connect("activate", self.on_exit)
        menu.append(item_quit)
        
        menu.show_all()
        self.indicator.set_menu(menu)
        
        # ホットキー設定
        self.hotkey_mode = self.config.get("hotkey_mode", "toggle")
        self.setup_hotkey()
        
        # プリロード
        self.overlay_mgr.ensure_running()
        self.worker_mgr.ensure_running()
        
        print(f"--- STT Daemon (AppIndicator) ---")
        
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

    def _startup_mic_check(self):
        """起動時のマイクチェック（バックグラウンド実行）"""
        import i18n
        try:
            import mic_checker
        except ImportError:
            print("mic_checker module not found, skipping mic check")
            return
        
        lang = self.config.get("ui_language", "ja")
        sample_rate = self.config.get("sample_rate", 44100)
        preferred = self.config.get("default_device_index")
        
        print(f"Mic check: preferred device = {preferred}")
        result = mic_checker.find_working_device(preferred_index=preferred, sample_rate=sample_rate)
        
        if result["device_index"] is not None and not result["fallback"]:
            # 正常
            msg = i18n.get_text("mic_check_ok", lang, name=result["device_name"])
            print(f"Mic check: {msg}")
        elif result["fallback"]:
            # フォールバック発生 → 設定を更新して通知
            self.config["device_index"] = result["device_index"]
            config_manager.save_config(self.config)
            
            msg = i18n.get_text("mic_check_fallback", lang,
                               name=result["preferred_name"],
                               new_name=result["device_name"])
            print(f"Mic check: {msg}")
            self._send_notification("STT - Mic Check", msg, "warning")
        else:
            # 全滅
            msg = i18n.get_text("mic_check_no_device", lang)
            print(f"Mic check: {msg}")
            self._send_notification("STT - Mic Check", msg, "error")
    
    def _send_notification(self, title, message, urgency="normal"):
        """デスクトップ通知を送信"""
        try:
            cmd = ["notify-send", "-u", urgency, "-i", ICON_PATH, title, message]
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"Notification error: {e}")

    def on_activate(self):
        """Toggle mode の動作"""
        if self.recording:
            print("Hotkey: STOP (Toggle)")
            self.worker_mgr.send_command("STOP")
            self.recording = False
        else:
            print("Hotkey: START (Toggle)")
            self.worker_mgr.send_command("START")
            self.recording = True

    def on_press_hold(self):
        """Hold mode の開始動作"""
        if not self.recording:
            print("Hotkey: START (Hold)")
            self.worker_mgr.send_command("START")
            self.recording = True

    def on_release_hold(self):
        """Hold mode の終了動作"""
        if self.recording:
            print("Hotkey: STOP (Hold)")
            self.worker_mgr.send_command("STOP")
            self.recording = False

    def setup_hotkey(self):
        try:
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
            
            print(f"Hotkey Listener Started: {self.hotkey} (Mode: {self.hotkey_mode})")
            self.overlay_mgr.send_command("READY")
        except Exception as e:
            print(f"Hotkey Error: {e}")

    def reload_config(self):
        print("Reloading configuration...")
        try:
            self.config = config_manager.load_config()
            new_hotkey = self.config.get("hotkey", "<ctrl>+<shift>+<space>")
            new_mode = self.config.get("hotkey_mode", "toggle")
            
            if new_hotkey != self.hotkey or new_mode != self.hotkey_mode:
                print(f"Hotkey updated: {self.hotkey}({self.hotkey_mode}) -> {new_hotkey}({new_mode})")
                self.hotkey = new_hotkey
                self.hotkey_mode = new_mode
                if self.listener:
                    self.listener.stop()
                self.setup_hotkey()

            self.worker_mgr.restart()
            self.overlay_mgr.cleanup()
            self.overlay_mgr.ensure_running()
            
            # メニューを再構築（言語変更の反映）
            GLib.idle_add(self.rebuild_menu)
            
        except Exception as e:
            print(f"Reload failed: {e}")

    def on_settings(self, widget):
        def _run():
            print("Opening GUI...")
            try:
                subprocess.run([PYTHON_CMD, "gui.py"], cwd=os.path.dirname(os.path.abspath(__file__)))
                print("GUI closed.")
                GLib.idle_add(self.reload_config)
            except Exception as e:
                print(f"GUI Error: {e}")
        threading.Thread(target=_run, daemon=True).start()

    def on_exit(self, widget):
        print("Exiting...")
        if self.listener:
            self.listener.stop()
        self.worker_mgr.cleanup()
        self.overlay_mgr.cleanup()
        Gtk.main_quit()

    def run(self):
        # シグナルハンドラ設定
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        # SIGUSR1: GUIからの設定再読み込みシグナル
        signal.signal(signal.SIGUSR1, lambda sig, frame: GLib.idle_add(self.reload_config))
        Gtk.main()

if __name__ == "__main__":
    # Prevent double execution
    lock_socket = check_singleton()
    
    app = STTDaemonAppIndicator()
    app.run()
