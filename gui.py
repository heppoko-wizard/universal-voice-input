import flet as ft
import config_manager
import os

def main(page: ft.Page):
    page.title = "Speech-to-Text Settings"
    page.window_width = 500
    page.window_height = 700
    page.scroll = "auto"
    page.theme_mode = ft.ThemeMode.DARK # Modern dark theme

    config = config_manager.load_config()
    devices = config_manager.get_input_devices()

    # --- UI Elements ---
    
    # API Keys Section
    api_groq = ft.TextField(label="Groq API Key", password=True, can_reveal_password=True, value=config["api_keys"].get("groq", ""))
    api_openai = ft.TextField(label="OpenAI API Key", password=True, can_reveal_password=True, value=config["api_keys"].get("openai", ""))
    
    # Local Inference UI
    cb_local = ft.Checkbox(label="Use Local Model (Offline)", value=config.get("use_local_model", False))
    sw_always_loaded = ft.Switch(label="Keep Model Loaded (Faster Response)", value=config.get("local_always_loaded", True))
    sw_ram_cache = ft.Switch(label="Force RAM Cache (Keep files in memory)", value=config.get("local_ram_cache", False))
    
    dd_local_device = ft.Dropdown(
        label="Inference Device",
        options=[
            ft.dropdown.Option("cpu", "CPU"),
            ft.dropdown.Option("cuda", "GPU (CUDA)"),
        ],
        value=config.get("local_device", "cpu")
    )
    
    # Compute type is now auto-selected based on device (int8 for CPU, float16 for GPU)
    
    dd_local_model = ft.Dropdown(
        label="Local Model Size",
        options=[
            ft.dropdown.Option("tiny"),
            ft.dropdown.Option("base"),
            ft.dropdown.Option("small"),
            ft.dropdown.Option("medium"),
            ft.dropdown.Option("large-v3"),
            # Assuming these will be auto-converted or downloaded if valid Hf Hub IDs
            ft.dropdown.Option("kotoba-tech/kotoba-whisper-v1.0-faster", "Kotoba-Whisper v1.0 (Japanese Optimized)"),
            ft.dropdown.Option("kotoba-tech/kotoba-whisper-v2.0-faster", "Kotoba-Whisper v2.0 (Japanese Optimized)"),
        ],
        value=config.get("local_model_size", "base")
    )
    
    # Device Selection
    device_options = [ft.dropdown.Option(key="default", text="Default System Device")]
    for d in devices:
        device_options.append(ft.dropdown.Option(key=str(d["id"]), text=f"{d['name']}"))
    
    current_device = str(config.get("device_index")) if config.get("device_index") is not None else "default"
    # Handle case where saved device index no longer exists
    if not any(d.key == current_device for d in device_options):
        current_device = "default"
        
    dd_device = ft.Dropdown(
        label="Microphone Device",
        options=device_options,
        value=current_device,
    )

    # Audio Settings
    dd_sample_rate = ft.Dropdown(
        label="Sample Rate",
        options=[
            ft.dropdown.Option("16000"),
            ft.dropdown.Option("44100"),
            ft.dropdown.Option("48000"),
        ],
        value=str(config.get("sample_rate", 44100))
    )
    
    dd_language = ft.Dropdown(
        label="Language",
        options=[
            ft.dropdown.Option("ja", "Japanese"),
            ft.dropdown.Option("en", "English"),
        ],
        value=config.get("language", "ja")
    )

    # Speed Up Factor
    txt_speed = ft.TextField(
        label="Speed Up Factor (e.g. 2.0 = 2x faster)", 
        value=str(config.get("speed_factor", 2.0)),
        keyboard_type=ft.KeyboardType.NUMBER
    )

    # Toggles
    sw_clipboard = ft.Switch(label="Restore Clipboard after typing", value=config.get("clipboard_restore", False))

    # Hotkey (Simple Text Input for now)
    txt_hotkey = ft.TextField(label="Global Hotkey (e.g. <ctrl>+<alt>+<space>)", value=config.get("hotkey", "<ctrl>+<alt>+<space>"))

    # Status Text
    status_text = ft.Text(value="Settings loaded.", color="green")

    def save_settings(e):
        try:
            # Update config dict
            config["api_keys"]["groq"] = api_groq.value
            config["api_keys"]["openai"] = api_openai.value
            
            if dd_device.value == "default":
                config["device_index"] = None
            else:
                try:
                    config["device_index"] = int(dd_device.value)
                except ValueError:
                    # It's a PulseAudio name (string)
                    config["device_index"] = dd_device.value
            
            config["sample_rate"] = int(dd_sample_rate.value)
            config["language"] = dd_language.value
            try:
                config["speed_factor"] = float(txt_speed.value)
            except ValueError:
                config["speed_factor"] = 1.0 # Fallback
                
            config["clipboard_restore"] = sw_clipboard.value
            config["hotkey"] = txt_hotkey.value
            
            # Local Config
            config["use_local_model"] = cb_local.value
            config["local_always_loaded"] = sw_always_loaded.value
            config["local_ram_cache"] = sw_ram_cache.value
            config["local_device"] = dd_local_device.value
            # compute_type is now auto-selected in transcriber based on device
            config["local_model_size"] = dd_local_model.value
            
            config_manager.save_config(config)
            
            status_text.value = "Settings saved! Restart the tool to apply."
            status_text.color = "blue"
            page.update()
            
        except Exception as ex:
            status_text.value = f"Error saving: {ex}"
            status_text.color = "red"
            page.update()

    # Save Button
    btn_save = ft.ElevatedButton("Save Settings", on_click=save_settings, icon="save")

    # --- Logic for Download ---
    
    download_progress = ft.ProgressRing(visible=False)
    download_status = ft.Text(value="", color="blue")
    
    def run_download(model_size):
        try:
            # Import here to avoid early crash if not installed, though we expect it is
            from faster_whisper import download_model
            
            # Special handling for custom paths/IDs if needed in future
            # For now directly pass the value
            print(f"Downloading {model_size}...")
            download_model(model_size)
            
            page.run_task(handle_download_success)
        except Exception as e:
            print(f"Download failed: {e}")
            page.run_task(lambda: handle_download_error(str(e)))

    async def handle_download_success():
        download_progress.visible = False
        download_status.value = "Download Complete! Ready to use."
        download_status.color = "green"
        btn_download.disabled = False
        page.update()

    async def handle_download_error(err_msg):
        download_progress.visible = False
        download_status.value = f"Error: {err_msg}"
        download_status.color = "red"
        btn_download.disabled = False
        page.update()

    def on_download_click(e):
        model_size = dd_local_model.value
        if not model_size:
            return
            
        btn_download.disabled = True
        download_progress.visible = True
        download_status.value = f"Downloading {model_size}... (This may take a while)"
        download_status.color = "blue"
        page.update()
        
        # Run in thread
        import threading
        threading.Thread(target=run_download, args=(model_size,), daemon=True).start()

    btn_download = ft.ElevatedButton("Pre-download Selected Model", on_click=on_download_click, icon="download")


    # Layout
    page.add(
        ft.Text("API Configuration", size=20, weight="bold"),
        api_groq,
        api_openai,
        ft.Divider(),
        
        ft.Text("Local Inference (CPU/Faster-Whisper)", size=20, weight="bold"),
        cb_local,
        sw_always_loaded,
        sw_ram_cache,
        dd_local_device,
        dd_local_model,
        ft.Row([btn_download, download_progress], alignment="start", vertical_alignment="center"),
        download_status,
        ft.Divider(),
        
        ft.Text("Audio Settings", size=20, weight="bold"),
        dd_device,
        ft.Row([dd_sample_rate, dd_language], alignment="spaceBetween"),
        txt_speed,
        ft.Divider(),
        
        ft.Text("Behavior", size=20, weight="bold"),
        txt_hotkey,
        sw_clipboard,
        ft.Divider(),
        
        ft.Row([btn_save], alignment="center"),
        ft.Row([status_text], alignment="center"),
    )

    # Flet app entry point

if __name__ == "__main__":
    ft.app(main)
