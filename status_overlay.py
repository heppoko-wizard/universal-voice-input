#!/usr/bin/env python3
"""
Status Overlay (X11 Native)
python-xlibを使用してX11ウィンドウを直接制御
Tkinterの環境依存問題を回避するための実装
"""
import sys
import threading
import time
from Xlib import X, display, Xutil

# Debug logging
def log(msg):
    try:
        with open("/tmp/overlay_debug.log", "a") as f:
            f.write(f"{time.strftime('%H:%M:%S')} - {msg}\n")
    except: pass

class X11BorderWindow:
    def __init__(self, disp, screen, x, y, w, h):
        self.disp = disp
        self.root = screen.root
        
        # ウィンドウ作成
        self.window = self.root.create_window(
            x, y, w, h, 0,
            screen.root_depth,
            X.InputOutput,
            X.CopyFromParent,
            background_pixel=screen.black_pixel,
            override_redirect=True,  # ウィンドウマネージャーの制御を受けない
            event_mask=X.ExposureMask
        )
        
        # 最前面に設定
        self.window.change_property(
            disp.intern_atom('_NET_WM_STATE'),
            disp.intern_atom('ATOM'), 32,
            [disp.intern_atom('_NET_WM_STATE_ABOVE')]
        )
        
        # 透過度設定 (70% = 0.7 * 0xFFFFFFFF)
        opacity = int(0.7 * 0xFFFFFFFF)
        self.window.change_property(
            disp.intern_atom('_NET_WM_WINDOW_OPACITY'),
            disp.intern_atom('CARDINAL'), 32,
            [opacity]
        )
        
        self.visible = False
        
    def set_color(self, color_name):
        """色を設定"""
        colormap = self.disp.screen().default_colormap
        
        color_map = {
            'red': colormap.alloc_named_color('red').pixel,
            'yellow': colormap.alloc_named_color('yellow').pixel,
            'black': self.disp.screen().black_pixel
        }
        
        pixel = color_map.get(color_name, self.disp.screen().black_pixel)
        self.window.change_attributes(background_pixel=pixel)
        self.window.clear_area(0, 0, 0, 0)  # 再描画
        
    def show(self):
        if not self.visible:
            self.window.map()
            self.visible = True
            
    def hide(self):
        if self.visible:
            self.window.unmap()
            self.visible = False

class StatusOverlay:
    def __init__(self):
        log("Initializing X11 Overlay...")
        
        self.disp = display.Display()
        self.screen = self.disp.screen()
        
        screen_width = self.screen.width_in_pixels
        screen_height = self.screen.height_in_pixels
        log(f"Screen: {screen_width}x{screen_height}")
        
        # 枠のサイズ設定
        padding = 100
        size_w = min(1000, screen_width - padding)
        size_h = min(1000, screen_height - padding)
        
        x = (screen_width - size_w) // 2
        y = (screen_height - size_h) // 2
        
        thickness = 3
        
        # 4つのボーダーウィンドウを作成
        self.borders = [
            X11BorderWindow(self.disp, self.screen, x, y, size_w, thickness),  # Top
            X11BorderWindow(self.disp, self.screen, x, y + size_h - thickness, size_w, thickness),  # Bottom
            X11BorderWindow(self.disp, self.screen, x, y, thickness, size_h),  # Left
            X11BorderWindow(self.disp, self.screen, x + size_w - thickness, y, thickness, size_h)  # Right
        ]
        
        self.disp.flush()
        self.running = True
        
        # コマンド監視スレッド
        threading.Thread(target=self._monitor_stdin, daemon=True).start()
        
        log(f"X11 Overlay started: {size_w}x{size_h}, thickness={thickness}")
        
    def set_color(self, color):
        """全ボーダーの色を変更"""
        log(f"Set Color: {color}")
        
        if color == "NONE":
            for border in self.borders:
                border.hide()
        else:
            for border in self.borders:
                border.set_color(color)
                border.show()
        
        self.disp.flush()
        
    def _monitor_stdin(self):
        """標準入力からコマンドを読む"""
        while self.running:
            try:
                line = sys.stdin.readline()
                if not line: break
                
                cmd = line.strip().upper()
                log(f"Received CMD: {cmd}")
                
                if cmd == "REC":
                    self.set_color("red")
                elif cmd == "PROC_LOCAL":
                    self.set_color("yellow")
                elif cmd == "PROC_ONLINE":
                    self.set_color("cyan")  # 青色
                elif cmd == "READY":
                    self.set_color("NONE")
                elif cmd == "QUIT":
                    self.running = False
                    break
            except Exception as e:
                log(f"Error: {e}")
                break
                
    def run(self):
        """イベントループ"""
        try:
            while self.running:
                # X11イベント処理（必要に応じて）
                while self.disp.pending_events():
                    event = self.disp.next_event()
                    # 必要に応じてイベント処理
                    
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            # クリーンアップ
            for border in self.borders:
                border.hide()
            self.disp.close()

if __name__ == "__main__":
    app = StatusOverlay()
    app.run()
