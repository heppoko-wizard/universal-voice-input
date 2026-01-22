import flet as ft
import config_manager
import os
import threading
import i18n

def main(page: ft.Page):
    config = config_manager.load_config()
    lang = config.get("ui_language", "ja")
    
    def t(key, **kwargs):
        return i18n.get_text(key, lang, **kwargs)

    page.title = t("title")
    page.window.width = 600
    page.window.height = 800
    page.scroll = "auto"
    page.theme_mode = ft.ThemeMode.DARK
    
    devices = config_manager.get_input_devices()

    # --- UI Elements ---
    
    # API Keys
    api_groq = ft.TextField(label=t("groq_key"), password=True, can_reveal_password=True, value=config["api_keys"].get("groq", ""))
    
    # Local Inference settings
    cb_local = ft.Checkbox(label=t("use_local"), value=config.get("use_local_model", True))
    
    # Memory Management Settings
    current_timeout = config.get("local_model_timeout", -1)
    
    # 内部管理用ステート
    is_infinite = (current_timeout == -1)
    slider_val = current_timeout if current_timeout > 0 else 0
    
    txt_timeout_label = ft.Text(t("timeout_label"), size=16)
    
    def update_timeout_label():
        if cb_infinite.value:
            txt_timeout_label.value = f"{t('timeout_label')}: {t('timeout_always')}"
        elif slider_timeout.value == 0:
            txt_timeout_label.value = f"{t('timeout_label')}: {t('timeout_zero')}"
        else:
            txt_timeout_label.value = f"{t('timeout_label')}: {t('timeout_hybrid', s=int(slider_timeout.value))}"
        page.update()

    def on_slider_change(e):
        update_timeout_label()
        
    def on_infinite_change(e):
        slider_timeout.disabled = cb_infinite.value
        update_timeout_label()
        page.update()

    slider_timeout = ft.Slider(
        min=0, max=300, divisions=30, label="{value}s",
        value=slider_val,
        on_change=on_slider_change,
        disabled=is_infinite
    )
    
    cb_infinite = ft.Checkbox(
        label=t("always_loaded"), 
        value=is_infinite,
        on_change=on_infinite_change
    )
    
    # 初期ラベルの適用
    update_timeout_label()

    # Audio Settings
    txt_speed = ft.TextField(
        label=t("speed_factor"), 
        value=str(config.get("speed_factor", 1.0)),
        keyboard_type=ft.KeyboardType.NUMBER,
        hint_text=t("speed_hint")
    )

    # UI Language Selection
    lang_options = [ft.dropdown.Option(key=opt["key"], text=opt["text"]) for opt in i18n.get_language_options()]
    dd_lang = ft.Dropdown(
        label=t("ui_language"),
        options=lang_options,
        value=lang,
    )

    # Model Path
    txt_model_path = ft.TextField(label=t("model_path"), value=config.get("local_model_size", "models/kotoba-whisper-v2.2-int8"), read_only=True)
    
    # Device Selection
    device_options = [ft.dropdown.Option(key="default", text="Default System Device")]
    for d in devices:
        device_options.append(ft.dropdown.Option(key=str(d["id"]), text=f"{d['name']}"))
    
    current_device = str(config.get("device_index")) if config.get("device_index") is not None else "default"
    if not any(d.key == current_device for d in device_options):
        current_device = "default"
        
    dd_device = ft.Dropdown(
        label=t("mic_device"),
        options=device_options,
        value=current_device,
    )

    # Hotkey
    txt_hotkey = ft.TextField(label=t("hotkey"), value=config.get("hotkey", "<ctrl>+<shift>+<space>"))

    # Status
    status_text = ft.Text(value=t("status_ready"), color="green")

    def save_settings(e):
        try:
            config["api_keys"]["groq"] = api_groq.value
            config["ui_language"] = dd_lang.value
            
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
            
            status_text.value = t("status_saved")
            status_text.color = "blue"
            page.update()
            
            import time
            time.sleep(1.0)
            page.window.close()
            
        except Exception as ex:
            status_text.value = t("status_error", e=ex)
            status_text.color = "red"
            page.update()

    btn_save = ft.ElevatedButton(t("btn_save"), on_click=save_settings, icon="save")
    
    # Model Setup Utility
    def run_converter(e):
        def _task():
            import subprocess
            try:
                txt_console.value = t("console_start")
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
                    txt_console.value += t("console_success")
                else:
                    txt_console.value += t("console_failed", code=process.returncode)
                    stderr = process.stderr.read()
                    txt_console.value += t("console_error", error=stderr)
                
                page.update()

            except Exception as ex:
                txt_console.value += f"\nException: {ex}"
                page.update()

        threading.Thread(target=_task, daemon=True).start()

    btn_convert = ft.ElevatedButton(t("btn_convert"), on_click=run_converter, icon="download")
    txt_console = ft.Text(value="", font_family="Consolas", size=12)

    # Layout
    page.add(
        ft.Text(t("title"), size=24, weight="bold"),
        ft.Divider(),
        ft.Text(t("api_settings"), size=18, weight="bold"),
        dd_lang,
        api_groq,
        dd_device,
        txt_hotkey,
        txt_speed,
        ft.Divider(),
        ft.Text(t("local_model_settings"), size=18, weight="bold"),
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
