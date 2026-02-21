#!/usr/bin/env python3
"""
Status Overlay (Cross-Platform)
Tkinterを用いて画面の四辺に枠線を描画するオーバーレイ。
X11非依存でWindows/macOS/Linuxすべてで動作するよう設計。
"""
import sys
import threading
import time
import tkinter as tk
import platform

class CrossPlatformOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw() # Main window is hidden

        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Border settings
        padding = 50 if platform.system() == "Darwin" else 0  # Avoid macOS menu bar if 0 padding is problematic
        self.thickness = 4
        
        # OS specific transparency and click-through
        self.bg_color = "black"
        self.trans_color = "black"
        
        if platform.system() == "Windows":
            self.root.wm_attributes("-transparentcolor", self.trans_color)
            self.root.attributes("-alpha", 0.7)
        elif platform.system() == "Darwin": # macOS
            self.root.wm_attributes("-transparent", True)
            self.bg_color = 'systemTransparent'
        else: # Linux/X11/Wayland
            self.root.wait_visibility(self.root)
            self.root.attributes("-alpha", 0.7)
            
        self.borders = []
        
        # Geometry setup for 4 edges
        edges = [
            (0, padding, screen_width, self.thickness), # Top
            (0, screen_height - self.thickness - padding, screen_width, self.thickness), # Bottom
            (0, padding, self.thickness, screen_height - (padding*2)), # Left
            (screen_width - self.thickness, padding, self.thickness, screen_height - (padding*2)) # Right
        ]
        
        for (x, y, w, h) in edges:
            top = tk.Toplevel(self.root)
            top.geometry(f"{w}x{h}+{x}+{y}")
            top.overrideredirect(True) # No window manager framing
            top.attributes("-topmost", True) # Always on top
            top.configure(background=self.bg_color)
            
            # Click-through depending on OS
            if platform.system() == "Windows":
                top.wm_attributes("-transparentcolor", self.trans_color)
                # Windows click-through WS_EX_TRANSPARENT | WS_EX_LAYERED
                import ctypes
                hwnd = ctypes.windll.user32.GetParent(top.winfo_id())
                style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
                ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x80000 | 0x20)
            elif platform.system() == "Darwin":
                pass # Handled differently, or usually TopLevel empty space passes through
            else:
                top.attributes("-alpha", 0.7)
                
            top.withdraw() # Hidden initially
            self.borders.append(top)

        self.running = True
        
        # Start stdin monitor in background
        threading.Thread(target=self._monitor_stdin, daemon=True).start()

    def set_color(self, color):
        """四辺の枠の色を変更し、表示/非表示を切り替える"""
        if color == "NONE":
            for b in self.borders:
                b.withdraw()
        else:
            for b in self.borders:
                b.configure(background=color)
                b.deiconify()

    def _monitor_stdin(self):
        while self.running:
            try:
                line = sys.stdin.readline()
                if not line: break
                
                cmd = line.strip().upper()
                
                # GUI thread safe call
                if cmd == "REC":
                    self.root.after(0, self.set_color, "red")
                elif cmd == "PROC_LOCAL":
                    self.root.after(0, self.set_color, "yellow")
                elif cmd == "PROC_ONLINE":
                    self.root.after(0, self.set_color, "cyan")
                elif cmd == "READY":
                    self.root.after(0, self.set_color, "NONE")
                elif cmd == "QUIT":
                    self.running = False
                    self.root.after(0, self.root.quit)
                    break
            except Exception as e:
                break

    def run(self):
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            pass
        finally:
            self.root.destroy()

if __name__ == "__main__":
    app = CrossPlatformOverlay()
    app.run()
