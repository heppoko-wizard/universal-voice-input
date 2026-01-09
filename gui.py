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
    sw_clipboard = ft.Switch(label="Restore Clipboard after typing", value=config.get("clipboard_restore", True))

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
                config["device_index"] = int(dd_device.value)
            
            config["sample_rate"] = int(dd_sample_rate.value)
            config["language"] = dd_language.value
            try:
                config["speed_factor"] = float(txt_speed.value)
            except ValueError:
                config["speed_factor"] = 1.0 # Fallback
                
            config["clipboard_restore"] = sw_clipboard.value
            config["hotkey"] = txt_hotkey.value
            
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

    # Layout
    page.add(
        ft.Text("API Configuration", size=20, weight="bold"),
        api_groq,
        api_openai,
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

ft.app(target=main)
