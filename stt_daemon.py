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
        menu = Gtk.Menu()
        
        item_settings = Gtk.MenuItem(label="Settings")
        item_settings.connect("activate", self.on_settings)
        menu.append(item_settings)
        
        item_quit = Gtk.MenuItem(label="Exit")
        item_quit.connect("activate", self.on_exit)
        menu.append(item_quit)
        
        menu.show_all()
        self.indicator.set_menu(menu)
        
        # プリロード
        self.overlay_mgr.ensure_running()
        self.worker_mgr.ensure_running()
        
        # ホットキー設定
        self.setup_hotkey()
        
        print(f"--- STT Daemon (AppIndicator) ---")
        
    def on_worker_status(self, status):
        self.overlay_mgr.send_command(status)

    def on_activate(self):
        if self.recording:
            print("Hotkey: STOP")
            self.worker_mgr.send_command("STOP")
            self.recording = False
        else:
            print("Hotkey: START")
            self.worker_mgr.send_command("START")
            self.recording = True

    def setup_hotkey(self):
        try:
            self.listener = keyboard.GlobalHotKeys({
                self.hotkey: self.on_activate
            })
            self.listener.start()
            print(f"Hotkey Listener Started: {self.hotkey}")
            self.overlay_mgr.send_command("READY")
        except Exception as e:
            print(f"Hotkey Error: {e}")

    def reload_config(self):
        print("Reloading configuration...")
        try:
            self.config = config_manager.load_config()
            new_hotkey = self.config.get("hotkey", "<ctrl>+<shift>+<space>")
            
            if new_hotkey != self.hotkey:
                print(f"Hotkey changed: {self.hotkey} -> {new_hotkey}")
                self.hotkey = new_hotkey
                if self.listener:
                    self.listener.stop()
                self.listener = keyboard.GlobalHotKeys({
                    self.hotkey: self.on_activate
                })
                self.listener.start()

            self.worker_mgr.restart()
            self.overlay_mgr.cleanup()
            self.overlay_mgr.ensure_running()
            
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
        Gtk.main()

if __name__ == "__main__":
    # Prevent double execution
    lock_socket = check_singleton()
    
    app = STTDaemonAppIndicator()
    app.run()
