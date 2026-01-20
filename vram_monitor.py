#!/usr/bin/env python3
"""
VRAM Monitor - リアルタイムGPU VRAM使用状況監視ツール
更新頻度を調整可能で、軽量動作を実現
"""

import flet as ft
import subprocess
import threading
import time
import sys

class VRAMMonitor:
    def __init__(self, page: ft.Page):
        self.page = page
        self.running = True
        self.update_interval = 1.0  # 初期値: 1秒
        
        # UI要素
        self.vram_text = ft.Text(value="VRAM: 取得中...", size=20, weight="bold")
        self.gpu_name_text = ft.Text(value="GPU: 検出中...", size=14)
        self.temp_text = ft.Text(value="温度: --°C", size=14)
        self.utilization_text = ft.Text(value="使用率: --%", size=14)
        self.progress_bar = ft.ProgressBar(width=400, value=0)
        
        self.interval_slider = ft.Slider(
            min=0.1,
            max=5.0,
            value=self.update_interval,
            divisions=49,
            label="更新頻度: {value}秒",
            on_change=self.on_interval_change
        )
        
        self.status_text = ft.Text(value="監視中...", color="green", size=12)
        
    def on_interval_change(self, e):
        """更新頻度を変更"""
        self.update_interval = float(e.control.value)
        self.status_text.value = f"更新頻度を {self.update_interval:.1f}秒 に変更"
        self.page.update()
        
    def get_nvidia_smi_info(self):
        """nvidia-smiでGPU情報を取得"""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name,memory.used,memory.total,temperature.gpu,utilization.gpu',
                 '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                line = result.stdout.strip()
                parts = [p.strip() for p in line.split(',')]
                
                if len(parts) >= 5:
                    return {
                        'name': parts[0],
                        'used': float(parts[1]),
                        'total': float(parts[2]),
                        'temp': parts[3],
                        'util': parts[4]
                    }
        except Exception as e:
            print(f"nvidia-smi取得エラー: {e}")
        
        return None
    
    def update_loop(self):
        """バックグラウンドで定期的にGPU情報を更新"""
        while self.running:
            try:
                info = self.get_nvidia_smi_info()
                
                if info:
                    used_gb = info['used'] / 1024
                    total_gb = info['total'] / 1024
                    percent = (info['used'] / info['total']) * 100 if info['total'] > 0 else 0
                    
                    # UI更新（メインスレッドで実行）
                    def update_ui():
                        self.gpu_name_text.value = f"GPU: {info['name']}"
                        self.vram_text.value = f"VRAM: {used_gb:.2f} GB / {total_gb:.2f} GB"
                        self.temp_text.value = f"温度: {info['temp']}°C"
                        self.utilization_text.value = f"GPU使用率: {info['util']}%"
                        self.progress_bar.value = percent / 100
                        self.status_text.value = f"更新中... ({self.update_interval:.1f}秒間隔)"
                        self.status_text.color = "green"
                        self.page.update()
                    
                    self.page.run_task(update_ui)
                else:
                    def show_error():
                        self.vram_text.value = "VRAM: NVIDIA GPUが見つかりません"
                        self.status_text.value = "nvidia-smiが利用できません"
                        self.status_text.color = "red"
                        self.page.update()
                    
                    self.page.run_task(show_error)
                
            except Exception as e:
                print(f"更新エラー: {e}")
            
            # 指定された間隔でスリープ
            time.sleep(self.update_interval)
    
    def start_monitoring(self):
        """監視スレッドを開始"""
        thread = threading.Thread(target=self.update_loop, daemon=True)
        thread.start()
    
    def stop_monitoring(self):
        """監視を停止"""
        self.running = False

def main(page: ft.Page):
    page.title = "VRAM Monitor"
    page.window_width = 500
    page.window_height = 450
    page.theme_mode = ft.ThemeMode.DARK
    
    monitor = VRAMMonitor(page)
    
    # 終了ボタン
    def on_exit(e):
        monitor.stop_monitoring()
        page.window_destroy()
    
    btn_exit = ft.ElevatedButton(
        "終了",
        on_click=on_exit,
        icon="close",
        bgcolor="red",
        color="white"
    )
    
    # 強制キルボタン（即座にプロセスを終了）
    def on_force_kill(e):
        monitor.stop_monitoring()
        sys.exit(0)
    
    btn_force_kill = ft.ElevatedButton(
        "強制終了",
        on_click=on_force_kill,
        icon="power_settings_new",
        bgcolor="darkred",
        color="white"
    )
    
    # レイアウト
    page.add(
        ft.Container(
            content=ft.Column([
                ft.Text("🖥️ VRAM Monitor", size=24, weight="bold"),
                ft.Divider(),
                monitor.gpu_name_text,
                monitor.vram_text,
                monitor.progress_bar,
                monitor.temp_text,
                monitor.utilization_text,
                ft.Divider(),
                ft.Text("更新頻度調整", size=16, weight="bold"),
                monitor.interval_slider,
                ft.Text("更新頻度を上げるとGPU負荷が増加します", size=10, italic=True, color="gray"),
                ft.Divider(),
                monitor.status_text,
                ft.Row([btn_exit, btn_force_kill], alignment="center"),
            ], spacing=10, horizontal_alignment="center"),
            padding=20
        )
    )
    
    # 監視開始
    monitor.start_monitoring()
    
    # ウィンドウクローズ時のクリーンアップ
    def on_window_close(e):
        monitor.stop_monitoring()
    
    page.on_window_event = on_window_close

if __name__ == "__main__":
    ft.app(main)
