import sys
import os
import subprocess
import shutil

def get_platform():
    if sys.platform.startswith("linux"):
        return "linux"
    elif sys.platform == "darwin":
        return "mac"
    elif sys.platform == "win32":
        return "windows"
    return "unknown"



def play_sound(sound_type="start"):
    plat = get_platform()
    try:
        if plat == "linux":
            sounds = {
                "start": "/usr/share/sounds/freedesktop/stereo/camera-shutter.oga",
                "stop": "/usr/share/sounds/freedesktop/stereo/complete.oga",
                "error": "/usr/share/sounds/freedesktop/stereo/dialog-warning.oga"
            }
            path = sounds.get(sound_type)
            if path and os.path.exists(path):
                subprocess.Popen(["paplay", path], stderr=subprocess.DEVNULL)
        
        elif plat == "mac":
            # macOS system sounds
            sounds = {
                "start": "/System/Library/Sounds/Tink.aiff",
                "stop": "/System/Library/Sounds/Pop.aiff",
                "error": "/System/Library/Sounds/Basso.aiff"
            }
            path = sounds.get(sound_type)
            if path:
                subprocess.Popen(["afplay", path], stderr=subprocess.DEVNULL)
                
        elif plat == "windows":
            import winsound
            if sound_type == "start":
                winsound.Beep(1000, 200)
            elif sound_type == "stop":
                winsound.Beep(800, 200)
            else:
                winsound.MessageBeep(winsound.MB_ICONHAND)

    except Exception:
        pass

def copy_text(text):
    """Cross-platform copy."""
    # Try pyperclip first as it handles many cases
    try:
        import pyperclip
        # Linux Wayland fix
        if get_platform() == "linux" and os.environ.get("WAYLAND_DISPLAY"):
            if shutil.which("wl-copy"):
                p = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE)
                p.communicate(input=text.encode('utf-8'))
                return
        
        pyperclip.copy(text)
    except Exception as e:
        print(f"Copy failed: {e}")

def paste_text():
    """Simulate Ctrl+V / Cmd+V using pynput, falling back to OS commands."""
    plat = get_platform()
    try:
        from pynput.keyboard import Key, Controller
        keyboard = Controller()
        mod_key = Key.cmd if plat == "mac" else Key.ctrl
        keyboard.press(mod_key)
        keyboard.press('v')
        keyboard.release('v')
        keyboard.release(mod_key)
        return
    except Exception as e:
        print(f"Paste via pynput failed: {e}")
        
    try:
        if plat == "linux":
            # Use xdotool if available (X11/XWayland)
            if shutil.which("xdotool"):
                subprocess.run(["xdotool", "key", "--clearmodifiers", "ctrl+v"])
            else:
                print("xdotool not found.")
        
        elif plat == "mac":
            # AppleScript to send Cmd+V
            script = 'tell application "System Events" to keystroke "v" using command down'
            subprocess.run(["osascript", "-e", script])
            
        elif plat == "windows":
            pass
            
    except Exception as e:
        print(f"Paste fallback failed: {e}")



def type_text(text):
    """
    Simulate typing by copying text to clipboard and pasting.
    This is generally more reliable than simulating individual keystrokes for large text.
    """
    import time
    copy_text(text)
    # Wait a bit for clipboard to update
    time.sleep(0.1)
    paste_text()

def set_autostart(enabled: bool):
    """
    Enable or disable auto-start on login.
    Linux: systemd
    macOS: LaunchAgents
    Windows: Startup folder
    """
    plat = get_platform()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    try:
        if plat == "linux":
            # systemctl --user は setup_linux.sh で登録済みと仮定
            cmd = ["systemctl", "--user", "enable" if enabled else "disable", "stt-tool.service"]
            subprocess.run(cmd, check=False, stderr=subprocess.DEVNULL)
            
        elif plat == "mac":
            plist_path = os.path.expanduser("~/Library/LaunchAgents/com.stt-tool.plist")
            if os.path.exists(plist_path):
                # RunAtLoad を書き換えるか、load/unload で制御
                # ここではシンプルに load/unload (unloadしてもplistは残る)
                if enabled:
                    subprocess.run(["launchctl", "load", plist_path], check=False, stderr=subprocess.DEVNULL)
                else:
                    subprocess.run(["launchctl", "unload", plist_path], check=False, stderr=subprocess.DEVNULL)
                    
        elif plat == "windows":
            import winshell
            from win32com.client import Dispatch
            
            startup_path = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup")
            shortcut_path = os.path.join(startup_path, "Open-STT-Tool.lnk")
            
            if enabled:
                if not os.path.exists(shortcut_path):
                    # 起動用バッチファイル（ランチャー）があるはずなのでそれへのショートカットを作成
                    target = os.path.join(script_dir, "start_stt_gui.bat")
                    if os.path.exists(target):
                        shell = Dispatch('WScript.Shell')
                        shortcut = shell.CreateShortCut(shortcut_path)
                        shortcut.Targetpath = target
                        shortcut.WorkingDirectory = script_dir
                        shortcut.IconLocation = os.path.join(script_dir, "venv", "Scripts", "python.exe") + ",0"
                        shortcut.save()
            else:
                if os.path.exists(shortcut_path):
                    os.remove(shortcut_path)
    except Exception as e:
        print(f"Failed to set autostart: {e}")

