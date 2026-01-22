import flet as ft
import config_manager
import os
import threading

def main(page: ft.Page):
    page.title = "STT Config Editor"
    page.window.width = 600
    page.window.height = 800
    page.scroll = "auto"
    page.theme_mode = ft.ThemeMode.DARK
    
    config = config_manager.load_config()
    devices = config_manager.get_input_devices()

    # --- UI Elements ---
    
    # API Keys
    api_groq = ft.TextField(label="Groq API Key", password=True, can_reveal_password=True, value=config["api_keys"].get("groq", ""))
    
    # Local Inference settings
    cb_local = ft.Checkbox(label="Use Local Model", value=config.get("use_local_model", True))
    
    # Memory Management Settings
    current_timeout = config.get("local_model_timeout", -1)
    
    # 内部管理用ステート
    is_infinite = (current_timeout == -1)
    slider_val = current_timeout if current_timeout > 0 else 0
    
    txt_timeout_label = ft.Text("モデル保持時間: 常時保持 (最速)", size=16)
    
    def update_timeout_label():
        if cb_infinite.value:
            txt_timeout_label.value = "モデル保持時間: 常時保持 (最速)"
        elif slider_timeout.value == 0:
            txt_timeout_label.value = "モデル保持時間: 0秒 (即時解放 - メモリ節約)"
        else:
            txt_timeout_label.value = f"モデル保持時間: {int(slider_timeout.value)}秒 (ハイブリッド)"
        page.update()

    def on_slider_change(e):
        update_timeout_label()
        
    def on_infinite_change(e):
        slider_timeout.disabled = cb_infinite.value
        update_timeout_label()
        page.update()

    slider_timeout = ft.Slider(
        min=0, max=300, divisions=30, label="{value}秒",
        value=slider_val,
        on_change=on_slider_change,
        disabled=is_infinite
    )
    
    cb_infinite = ft.Checkbox(
        label="常時保持 (推奨)", 
        value=is_infinite,
        on_change=on_infinite_change
    )
    
    # 初期ラベル更新
    if not is_infinite and slider_val == 0:
         txt_timeout_label.value = "モデル保持時間: 0秒 (即時解放 - メモリ節約)"
    elif not is_infinite:
         txt_timeout_label.value = f"モデル保持時間: {int(slider_val)}秒 (ハイブリッド)"

    # Audio Settings
    txt_speed = ft.TextField(
        label="Speed Up Factor (e.g. 1.5)", 
        value=str(config.get("speed_factor", 1.0)),
        keyboard_type=ft.KeyboardType.NUMBER,
        hint_text="1.0 = Normal, 2.0 = Double Speed"
    )

    # Int8 Model Path
    txt_model_path = ft.TextField(label="Local Model Path", value=config.get("local_model_size", "models/kotoba-whisper-v2.2-int8"), read_only=True)
    
    # Device Selection
    device_options = [ft.dropdown.Option(key="default", text="Default System Device")]
    for d in devices:
        device_options.append(ft.dropdown.Option(key=str(d["id"]), text=f"{d['name']}"))
    
    current_device = str(config.get("device_index")) if config.get("device_index") is not None else "default"
    if not any(d.key == current_device for d in device_options):
        current_device = "default"
        
    dd_device = ft.Dropdown(
        label="Microphone Device",
        options=device_options,
        value=current_device,
    )

    # Hotkey
    txt_hotkey = ft.TextField(label="Global Hotkey", value=config.get("hotkey", "<ctrl>+<alt>+<space>"))

    # Status
    status_text = ft.Text(value="Ready.", color="green")

    def save_settings(e):
        try:
            config["api_keys"]["groq"] = api_groq.value
            
            if dd_device.value == "default":
                config["device_index"] = None
            else:
                try:
                    config["device_index"] = int(dd_device.value)
                except ValueError:
                    config["device_index"] = dd_device.value
            
            try:
                config["speed_factor"] = float(txt_speed.value)
            except ValueError:
                config["speed_factor"] = 1.0
            
            config["hotkey"] = txt_hotkey.value
            config["use_local_model"] = cb_local.value
            
            # Update optimized settings based on new simple logic
            if cb_infinite.value:
                config["local_model_timeout"] = -1
            else:
                config["local_model_timeout"] = int(slider_timeout.value)
            
            # Remove legacy keys
            legacy_keys = ["local_always_loaded", "local_ram_cache", "hybrid_mode", "hybrid_timeout"]
            for key in legacy_keys:
                if key in config:
                    del config[key]
            
            config["local_compute_type"] = "int8"
            config["local_model_size"] = txt_model_path.value
            
            config_manager.save_config(config)
            
            status_text.value = "Settings Saved. Restarting..."
            status_text.color = "blue"
            page.update()
            
            # デーモン側でGUIプロセス終了を検知してリロードするため、ここで閉じる
            import time
            time.sleep(1.0)
            page.window.close()
            
        except Exception as ex:
            status_text.value = f"Error saving: {ex}"
            status_text.color = "red"
            page.update()

    btn_save = ft.ElevatedButton("Save & Apply (Restart)", on_click=save_settings, icon="save")
    
    # Model Setup Utility
    def run_converter(e):
        # This is a helper to run the conversion script if needed
        def _task():
            import subprocess
            try:
                txt_console.value = "Starting conversion...\n"
                page.update()
                
                process = subprocess.Popen(
                    ["python", "convert_model.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=os.getcwd()
                )
                
                for line in process.stdout:
                    txt_console.value += line
                    page.update()
                    
                process.wait()
                if process.returncode == 0:
                    txt_console.value += "\nSUCCESS: Model converted."
                else:
                    txt_console.value += f"\nFAILED: Exit code {process.returncode}"
                    stderr = process.stderr.read()
                    txt_console.value += f"\nError: {stderr}"
                
                page.update()

            except Exception as ex:
                txt_console.value += f"\nException: {ex}"
                page.update()

        threading.Thread(target=_task, daemon=True).start()

    btn_convert = ft.ElevatedButton("Setup/Update Local Model (Downloads & Optimizes)", on_click=run_converter, icon="download")
    txt_console = ft.Text(value="", font_family="Consolas", size=12)

    # Layout
    page.add(
        ft.Text("STT Configuration", size=24, weight="bold"),
        ft.Divider(),
        ft.Text("General", size=18, weight="bold"),
        api_groq,
        dd_device,
        txt_hotkey,
        txt_speed,
        ft.Divider(),
        ft.Text("Local Model (Optimized)", size=18, weight="bold"),
        cb_local,
        ft.Container(height=10),
        txt_timeout_label,
        cb_infinite,
        slider_timeout,
        ft.Container(height=10),
        txt_model_path,
        btn_convert,
        ft.Container(
            content=txt_console,
            bgcolor=ft.Colors.BLACK54,
            padding=10,
            border_radius=5,
        ),
        ft.Divider(),
        ft.Row([btn_save], alignment="center"),
        ft.Row([status_text], alignment="center"),
    )

if __name__ == "__main__":
    ft.app(target=main)
