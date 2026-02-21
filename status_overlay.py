#!/usr/bin/env python3
"""
Status Overlay (Cross-Platform / Floating Bar)
Tkinterを用いて画面の上部・中央下・下部にフローティングステータスバーを表示する軽量なGUI。
録音中の時間カウント、待機状態・処理状態の視覚化を行う。
"""
import sys
import threading
import time
import tkinter as tk
import platform
import json
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(PROJECT_ROOT, "config.json")

def load_ui_position():
    try:
        with open(CONFIG_FILE, "r") as f:
            c = json.load(f)
            return c.get("ui_position", "bottom")
    except:
        return "bottom"

class FloatingOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True) # タイトルバーなし
        self.root.attributes("-topmost", True) # 常に最前面
        
        # クロスプラットフォームな透過処理とクリック透過対応
        plat = platform.system()
        if plat == "Windows":
            self.root.wm_attributes("-transparentcolor", "black")
            self.root.config(bg="black")
            bg_color = "black"
            # Click-through (WS_EX_TRANSPARENT | WS_EX_LAYERED)
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x80000 | 0x20)
        elif plat == "Darwin": # macOS
            self.root.wm_attributes("-transparent", True)
            self.root.config(bg="systemTransparent")
            bg_color = "systemTransparent"
        else: # Linux/X11/Wayland
            self.root.wait_visibility(self.root)
            self.root.attributes("-alpha", 0.8) # 全体に透明度をかけるため背景黒は不可
            self.root.config(bg="gray10")
            bg_color = "gray10"
            
        self.bg_color = bg_color
        
        # UIウィジェット
        self.label = tk.Label(
            self.root, 
            text="🎙️ 待機中", 
            font=("Arial", 12, "bold"),
            fg="white", 
            bg=self.bg_color,
            padx=15, 
            pady=5
        )
        self.label.pack()

        # 初期配置
        self._recenter_window()
        self.root.withdraw() # 初期は非表示

        self.running = True
        self.start_time = 0
        self.current_state = "READY"
        
        # Start stdin monitor in background
        threading.Thread(target=self._monitor_stdin, daemon=True).start()
        
        # タイマー更新ループ
        self._update_timer()

    def _recenter_window(self):
        self.root.update_idletasks()
        w = self.label.winfo_reqwidth()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        pos = load_ui_position()

        if pos == "top":
            x = (sw - w) // 2
            y = 20
        elif pos == "center":
            x = (sw - w) // 2
            y = sh - 300
        else: # bottom
            x = (sw - w) // 2
            y = sh - 80
            
        self.root.geometry(f"+{x}+{y}")

    def set_status(self, state):
        self.current_state = state
        if state == "READY":
            self.root.withdraw()
        else:
            if state == "REC":
                self.start_time = time.time()
                self.label.config(text="🔴 録音中 [00:00]", fg="#ff4444")
            elif state == "PROC_LOCAL":
                self.label.config(text="⏳ 処理中... (Local)", fg="#ffff44")
            elif state == "PROC_ONLINE":
                self.label.config(text="⏳ 処理中... (Online)", fg="#44eeff")
            elif state == "ERROR":
                self.label.config(text="⚠️ エラー発生", fg="red")
            
            
            # 再センタリング
            self._recenter_window()
            self.root.deiconify()

    def _update_timer(self):
        if self.running:
            if self.current_state == "REC":
                elapsed = int(time.time() - self.start_time)
                mins, secs = divmod(elapsed, 60)
                self.label.config(text=f"🔴 録音中 [{mins:02d}:{secs:02d}]")
                self._recenter_window()
            # 1秒（1000ms）ごとに再実行
            self.root.after(1000, self._update_timer)

    def _monitor_stdin(self):
        while self.running:
            try:
                line = sys.stdin.readline()
                if not line: break
                
                cmd = line.strip().upper()
                
                # GUI thread safe call
                if cmd == "REC":
                    self.root.after(0, self.set_status, "REC")
                elif cmd == "PROC_LOCAL":
                    self.root.after(0, self.set_status, "PROC_LOCAL")
                elif cmd == "PROC_ONLINE":
                    self.root.after(0, self.set_status, "PROC_ONLINE")
                elif cmd == "READY":
                    self.root.after(0, self.set_status, "READY")
                elif "ERROR" in cmd:
                    self.root.after(0, self.set_status, "ERROR")
                    time.sleep(2) # エラー表示を2秒残してREADYに戻る
                    self.root.after(0, self.set_status, "READY")
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
    app = FloatingOverlay()
    app.run()
