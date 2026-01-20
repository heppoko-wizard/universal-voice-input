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

def notify(title, message, replaces_id=None, timeout=3000):
    plat = get_platform()
    try:
        if plat == "linux":
            # -p: 通知IDを出力する
            # -t: タイムアウト（ミリ秒）、0 = 消えない
            cmd = ["notify-send", "-p", "-t", str(timeout)]
            if replaces_id:
                cmd.extend(["-r", str(replaces_id)])
            cmd.extend([title, message])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            new_id = result.stdout.strip()
            return new_id if new_id else replaces_id
        elif plat == "mac":
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(["osascript", "-e", script], stderr=subprocess.DEVNULL)
    except Exception:
        pass
    return replaces_id

def unnotify(notify_id):
    """通知を強制的に閉じる (Linux用)"""
    if not notify_id:
        return
    plat = get_platform()
    try:
        if plat == "linux":
            # DBusを使用して特定の通知IDを閉じる
            # uint32を指定して確実にマッチさせる
            subprocess.run([
                "dbus-send", "--type=method_call", "--dest=org.freedesktop.Notifications",
                "/org/freedesktop/Notifications", "org.freedesktop.Notifications.CloseNotification",
                f"uint32:{notify_id}"
            ], stderr=subprocess.DEVNULL)
    except Exception:
        pass

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
    """Simulate Ctrl+V / Cmd+V."""
    plat = get_platform()
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
            import ctypes
            # Simple Ctrl+V using user32.dll or pynput
            # Using pynput here is safer if installed
            from pynput.keyboard import Key, Controller
            keyboard = Controller()
            keyboard.press(Key.ctrl)
            keyboard.press('v')
            keyboard.release('v')
            keyboard.release(Key.ctrl)
            
    except Exception as e:
        print(f"Paste failed: {e}")

def get_hotkey_map(key_string):
    """Convert simplified hotkey string to pynput format if needed."""
    # Currently pynput handles <ctrl>+<shift> etc well on all platforms.
    # macOS might use <cmd> which maps to Key.cmd
    return key_string
