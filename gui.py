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
    
    # Optimization Mode Dropdown (順序: Local → CPU → Hybrid → Persistent)
    opt_mode_value = "zero"
    if config.get("local_always_loaded"):
        opt_mode_value = "always"
    elif config.get("hybrid_mode"):
        opt_mode_value = "hybrid"
    elif config.get("local_ram_cache"):
        opt_mode_value = "cpu"
        
    dd_opt_mode = ft.Dropdown(
        label="Optimization Mode",
        options=[
            ft.dropdown.Option("zero", "1. Zero Memory (毎回読込, VRAM 0MB)"),
            ft.dropdown.Option("cpu", "2. CPU Cache (効果薄, RAM 1.5GB)"),
            ft.dropdown.Option("hybrid", "3. Hybrid (自動消滅, 使用中のみVRAM)"),
            ft.dropdown.Option("always", "4. Persistent (常駐, VRAM 700MB)"),
        ],
        value=opt_mode_value,
        hint_text="Select how the model is managed in memory"
    )

    # Hybrid Timeout Slider (10秒単位, 10〜600秒)
    hybrid_timeout_val = config.get("hybrid_timeout", 300)
    slider_timeout = ft.Slider(
        min=10, max=600, divisions=59, label="{value}秒",
        value=hybrid_timeout_val,
    )
    txt_timeout_display = ft.Text(f"自動消滅: {hybrid_timeout_val}秒")
    
    def on_timeout_change(e):
        txt_timeout_display.value = f"自動消滅: {int(slider_timeout.value)}秒"
        page.update()
    slider_timeout.on_change = on_timeout_change
    
    hybrid_timeout_row = ft.Row(
        [txt_timeout_display, slider_timeout],
        visible=(opt_mode_value == "hybrid")
    )
    
    def on_mode_change(e):
        hybrid_timeout_row.visible = (dd_opt_mode.value == "hybrid")
        page.update()
    dd_opt_mode.on_change = on_mode_change

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
            
            # Update optimized settings based on mode
            mode = dd_opt_mode.value
            if mode == "zero":
                config["local_always_loaded"] = False
                config["local_ram_cache"] = False
                config["hybrid_mode"] = False
            elif mode == "cpu":
                config["local_always_loaded"] = False
                config["local_ram_cache"] = True
                config["hybrid_mode"] = False
            elif mode == "hybrid":
                config["local_always_loaded"] = False
                config["local_ram_cache"] = False
                config["hybrid_mode"] = True
                config["hybrid_timeout"] = int(slider_timeout.value)
            elif mode == "always":
                config["local_always_loaded"] = True
                config["local_ram_cache"] = False
                config["hybrid_mode"] = False
            
            config["local_compute_type"] = "int8"
            config["local_model_size"] = txt_model_path.value
            
            config_manager.save_config(config)
            
            status_text.value = "Settings Saved. Please restart the Daemon to apply."
            status_text.color = "blue"
            page.update()
            
        except Exception as ex:
            status_text.value = f"Error saving: {ex}"
            status_text.color = "red"
            page.update()

    btn_save = ft.ElevatedButton("Save Configuration", on_click=save_settings, icon="save")
    
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
        dd_opt_mode,
        hybrid_timeout_row,
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
