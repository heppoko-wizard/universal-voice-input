import flet as ft
import config_manager
import os
import threading
import i18n
import platform_utils

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
    
    # Online Provider Settings
    # LiteLLMの内部データベースからSTT対応モデルを動的取得
    try:
        import litellm as _litellm
        _all_models = _litellm.model_cost
        _stt_by_provider = {}
        for _m, _info in _all_models.items():
            if _info.get("mode") == "audio_transcription":
                _prov = _info.get("litellm_provider", "unknown")
                if _prov.startswith("one of"):
                    continue  # ドキュメント用サンプルを除外
                if _prov not in _stt_by_provider:
                    _stt_by_provider[_prov] = []
                _stt_by_provider[_prov].append(_m)
        # プロバイダごとにモデルをソート
        for _p in _stt_by_provider:
            _stt_by_provider[_p].sort()
    except Exception as _e:
        print(f"Failed to load LiteLLM model list: {_e}")
        _stt_by_provider = {
            "groq": ["groq/whisper-large-v3-turbo"],
            "openai": ["whisper-1"],
        }
    
    # model_costに未登録だがLiteLLMで実際に使えるプロバイダを手動追加
    # (Geminiはchatモードで音声入力を処理するためaudio_transcriptionとして登録されていない)
    _manual_providers = {
        "gemini": ["gemini/gemini-2.0-flash", "gemini/gemini-2.5-flash"],
    }
    for _mp, _models in _manual_providers.items():
        if _mp not in _stt_by_provider:
            _stt_by_provider[_mp] = _models
        else:
            for _m in _models:
                if _m not in _stt_by_provider[_mp]:
                    _stt_by_provider[_mp].append(_m)
            _stt_by_provider[_mp].sort()
    
    # プロバイダ表示名マッピング
    PROVIDER_LABELS = {
        "groq": "Groq",
        "openai": "OpenAI",
        "gemini": "Google Gemini",
        "azure": "Azure OpenAI",
        "deepgram": "Deepgram",
        "fireworks_ai": "Fireworks AI",
        "elevenlabs": "ElevenLabs",
        "ovhcloud": "OVHcloud",
        "assemblyai": "AssemblyAI",
        "watsonx": "IBM watsonx",
    }
    
    online_providers = config.get("online_providers", {})
    current_provider = config.get("online_provider", "groq")
    
    # プロバイダドロップダウン（動的に検出されたプロバイダ＋カスタム）
    provider_options = []
    for _prov_key in sorted(_stt_by_provider.keys()):
        _label = PROVIDER_LABELS.get(_prov_key, _prov_key)
        _count = len(_stt_by_provider[_prov_key])
        provider_options.append(ft.dropdown.Option(key=_prov_key, text=f"{_label} ({_count})"))
    provider_options.append(ft.dropdown.Option(key="custom", text=t("custom_endpoint")))
    
    provider_cfg = online_providers.get(current_provider, {})
    
    # UIウィジェットを先に作成
    txt_api_key = ft.TextField(
        label=t("api_key_label"),
        password=True, can_reveal_password=True,
        value=provider_cfg.get("api_key", ""),
    )
    
    # モデルドロップダウン
    def _build_model_options(prov):
        models = _stt_by_provider.get(prov, [])
        return [ft.dropdown.Option(key=m, text=m) for m in models]
    
    saved_model = provider_cfg.get("model", "")
    current_models = _stt_by_provider.get(current_provider, [])
    
    dd_online_model = ft.Dropdown(
        label=t("online_model_label"),
        options=_build_model_options(current_provider),
        value=saved_model if saved_model in current_models else (current_models[0] if current_models else None),
        visible=(current_provider != "custom"),
    )
    
    txt_custom_model_name = ft.TextField(
        label=t("online_model_label"),
        value=provider_cfg.get("model", "") if current_provider == "custom" else "",
        hint_text="openai/whisper-1",
        visible=(current_provider == "custom"),
    )
    
    txt_api_base = ft.TextField(
        label=t("api_base_label"),
        value=provider_cfg.get("api_base", ""),
        hint_text="http://localhost:8080/v1",
        visible=(current_provider == "custom"),
    )
    
    # 現在選択中のプロバイダを追跡
    _current_prov = [current_provider]
    
    # イベントハンドラ定義
    def on_provider_change(e):
        # 切り替え前: 現在の入力内容をメモリ上に保存
        old_prov = _current_prov[0]
        old_entry = {"api_key": txt_api_key.value}
        if old_prov == "custom":
            old_entry["model"] = txt_custom_model_name.value
            old_entry["api_base"] = txt_api_base.value
        else:
            old_entry["model"] = dd_online_model.value or ""
        online_providers[old_prov] = old_entry
        
        # 切り替え後
        prov = e.control.value
        _current_prov[0] = prov
        cfg = online_providers.get(prov, {})
        txt_api_key.value = cfg.get("api_key", "")
        
        is_custom = (prov == "custom")
        dd_online_model.visible = not is_custom
        txt_custom_model_name.visible = is_custom
        txt_api_base.visible = is_custom
        
        if is_custom:
            txt_custom_model_name.value = cfg.get("model", "")
            txt_api_base.value = cfg.get("api_base", "")
        else:
            models = _stt_by_provider.get(prov, [])
            dd_online_model.options = _build_model_options(prov)
            saved = cfg.get("model", "")
            dd_online_model.value = saved if saved in models else (models[0] if models else None)
        page.update()
    
    # on_selectをコンストラクタに直接渡したDropdownを作成 (Flet 0.80+: on_change→on_select)
    dd_provider = ft.Dropdown(
        label=t("online_provider"),
        options=provider_options,
        value=current_provider if any(o.key == current_provider for o in provider_options) else "groq",
        on_select=on_provider_change,
    )
    
    # Local Inference settings
    # Model Mode: online / local / custom
    # 後方互換: 古い use_local_model bool → model_mode 文字列
    raw_mode = config.get("model_mode")
    if raw_mode is None:
        raw_mode = "local" if config.get("use_local_model", True) else "online"
    
    rg_mode = ft.RadioGroup(
        value=raw_mode,
        content=ft.Row([
            ft.Radio(value="online", label=t("mode_online")),
            ft.Radio(value="local", label=t("mode_local")),
            ft.Radio(value="custom", label=t("mode_custom")),
        ]),
    )
    
    cb_punctuation = ft.Checkbox(
        label=t("add_punctuation"),
        value=config.get("add_punctuation", True)
    )

    cb_auto_start = ft.Checkbox(
        label=t("auto_start"),
        value=config.get("auto_start", False)
    )
    
    # Speed Factor
    speed_factor = config.get("speed_factor", 1.0)
    txt_speed = ft.TextField(
        label=t("speed_factor"),
        value=str(speed_factor),
        keyboard_type=ft.KeyboardType.NUMBER,
        hint_text=t("speed_hint")
    )

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

    # UI Language Selection
    lang_options = [ft.dropdown.Option(key=opt["key"], text=opt["text"]) for opt in i18n.get_language_options()]
    dd_lang = ft.Dropdown(
        label=t("ui_language"),
        options=lang_options,
        value=lang,
    )

    # Hotkey Mode Selection
    hotkey_mode = config.get("hotkey_mode", "toggle")
    dd_hotkey_mode = ft.Dropdown(
        label=t("hotkey_mode"),
        options=[
            ft.dropdown.Option(key="toggle", text=t("mode_toggle")),
            ft.dropdown.Option(key="hold", text=t("mode_hold")),
        ],
        value=hotkey_mode,
    )

    # Model Selection
    model_id = config.get("local_model_id", "RoachLin/kotoba-whisper-v2.2-faster")
    model_options = [ft.dropdown.Option(key=opt["key"], text=opt["text"]) for opt in i18n.get_model_options(lang)]
    
    preset_keys = [opt["key"] for opt in i18n.get_model_options(lang)]
    
    dd_model = ft.Dropdown(
        label=t("model_select"),
        options=model_options,
        value=model_id if model_id in preset_keys else preset_keys[0],
    )
    
    txt_custom_model = ft.TextField(
        label=t("custom_model"),
        hint_text=t("custom_model_hint"),
        value=model_id if raw_mode == "custom" else "",
    )
    
    # Device Selection
    current_device_index = config.get("device_index")
    is_manual_mic = current_device_index is not None
    
    cb_manual_mic = ft.Checkbox(
        label=t("mic_manual_select", default="マイクを手動で選択する (非推奨)"),
        value=is_manual_mic
    )
    
    device_options = []
    for d in devices:
        device_options.append(ft.dropdown.Option(key=str(d["id"]), text=d["name"]))
    
    current_device_str = str(current_device_index) if is_manual_mic else None
    if current_device_str and not any(d.key == current_device_str for d in device_options):
        current_device_str = None
        if device_options:
            current_device_str = device_options[0].key
            
    dd_device = ft.Dropdown(
        label=t("mic_device"),
        options=device_options,
        value=current_device_str,
        expand=True,
        visible=is_manual_mic,
    )

    def on_manual_mic_change(e):
        dd_device.visible = cb_manual_mic.value
        page.update()

    cb_manual_mic.on_change = on_manual_mic_change

    row_device = ft.Column([cb_manual_mic, dd_device])

    # Hotkey
    txt_hotkey = ft.TextField(label=t("hotkey"), value=config.get("hotkey", "<ctrl>+<shift>+<space>"))

    # Status (AppBarには短いステータスのみ)
    status_text = ft.Text(value=t("status_ready"), color="green", size=12)

    def show_dialog(title, message, color="green"):
        """結果をAlertDialogで表示"""
        dlg = ft.AlertDialog(
            title=ft.Text(title, weight="bold", color=color),
            content=ft.Text(message, selectable=True),
            actions=[ft.TextButton("OK", on_click=lambda e: _close_dlg(dlg))],
        )
        def _close_dlg(d):
            d.open = False
            page.update()
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    # 保存前の設定スナップショット
    import copy
    original_config = copy.deepcopy(config)

    def save_settings(e):
        import signal as sig
        import subprocess
        
        try:
            # オンラインプロバイダ設定の保存
            prov = dd_provider.value
            config["online_provider"] = prov
            if "online_providers" not in config:
                config["online_providers"] = {}
            config["online_providers"][prov] = {
                "api_key": txt_api_key.value,
                "model": txt_custom_model_name.value if prov == "custom" else dd_online_model.value,
            }
            if prov == "custom" and txt_api_base.value.strip():
                config["online_providers"][prov]["api_base"] = txt_api_base.value.strip()
            
            # 後方互換: 旧api_keysも更新
            if "api_keys" not in config:
                config["api_keys"] = {}
            config["api_keys"][prov] = txt_api_key.value
            
            config["ui_language"] = dd_lang.value
            config["hotkey_mode"] = dd_hotkey_mode.value
            config["add_punctuation"] = cb_punctuation.value
            config["auto_start"] = cb_auto_start.value
            
            # モデルモード
            mode = rg_mode.value
            config["model_mode"] = mode
            config["use_local_model"] = (mode != "online")  # 後方互換
            
            if mode == "custom":
                custom_val = txt_custom_model.value.strip()
                if not custom_val:
                    show_dialog("⚠️", t("custom_model_empty"), "red")
                    return
                if custom_val.startswith("/") or custom_val.startswith("~") or custom_val.startswith("."):
                    expanded = os.path.expanduser(custom_val)
                    if not os.path.isdir(expanded):
                        show_dialog("⚠️ " + t("status_error", e=""), t("model_path_not_found", path=custom_val), "red")
                        return
                    if not os.path.isfile(os.path.join(expanded, "model.bin")):
                        show_dialog("⚠️ " + t("status_error", e=""), t("model_bin_not_found", path=custom_val), "red")
                        return
                config["local_model_id"] = custom_val
            elif mode == "local":
                config["local_model_id"] = dd_model.value
            # online モードの場合は local_model_id を変更しない
            
            if not cb_manual_mic.value or not dd_device.value:
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
            
            # 変更差分を検出
            changes = []
            check_keys = [
                ("ui_language", t("ui_language")),
                ("hotkey", t("hotkey")),
                ("hotkey_mode", t("hotkey_mode")),
                ("device_index", t("mic_device")),
                ("model_mode", t("model_mode_label")),
                ("local_model_id", t("model_select")),
                ("local_model_timeout", t("timeout_label")),
                ("speed_factor", t("speed_factor")),
                ("add_punctuation", t("add_punctuation")),
                ("auto_start", t("auto_start")),
            ]
            for key, label in check_keys:
                old_val = original_config.get(key)
                new_val = config.get(key)
                if old_val != new_val:
                    changes.append(f"• {label}: {old_val} → {new_val}")
            
            # API Key (マスク表示)
            old_groq = original_config.get("api_keys", {}).get("groq", "")
            new_groq = config.get("api_keys", {}).get("groq", "")
            if old_groq != new_groq:
                changes.append(f"• {t('groq_key')}: ****")
            
            config_manager.save_config(config)
            
            # 自動起動の設定反映
            platform_utils.set_autostart(cb_auto_start.value)
            
            # デーモンにSIGUSR1を送信して再読み込み
            daemon_restarted = False
            try:
                result = subprocess.run(
                    ["pgrep", "-f", "stt_daemon.py"],
                    capture_output=True, text=True, timeout=3
                )
                pids = result.stdout.strip().split("\n")
                for pid_str in pids:
                    if pid_str.strip():
                        os.kill(int(pid_str.strip()), sig.SIGUSR1)
                        daemon_restarted = True
            except Exception:
                pass
            
            # ダイアログで結果表示
            if changes:
                msg = t("changes_applied") + "\n" + "\n".join(changes)
            else:
                msg = t("no_changes")
            
            if daemon_restarted:
                msg += "\n\n✅ " + t("daemon_restarted")
            else:
                msg += "\n\n⚠️ " + t("daemon_not_found")
            
            show_dialog("✅ " + t("status_saved"), msg)
            status_text.value = t("status_saved")
            status_text.color = "green"
            
            # スナップショットを更新
            original_config.clear()
            original_config.update(copy.deepcopy(config))
            
        except Exception as ex:
            show_dialog("❌ " + t("status_error", e=""), str(ex), "red")

    btn_save = ft.ElevatedButton(t("btn_save"), on_click=save_settings, icon="save")
    
    # Model Setup Utility
    def run_converter(e):
        def _task():
            import subprocess
            try:
                txt_console.value = t("console_start")
                page.update()
                
                # ドロップダウンで選択されているモデルIDを引数として渡す
                selected_model = dd_model.value
                process = subprocess.Popen(
                    ["python", "convert_model.py", selected_model],
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

    # --- Grouping & Layout Logic ---

    # 1. General Settings Group
    card_general = ft.Card(
        content=ft.Container(
            padding=15,
            content=ft.Column([
                ft.Text(t("api_settings"), size=18, weight="bold"),
                dd_lang,
                cb_auto_start,
            ])
        )
    )

    # 2. Input Settings Group
    card_input = ft.Card(
        content=ft.Container(
            padding=15,
            content=ft.Column([
                ft.Text(t("input_settings"), size=18, weight="bold"),
                row_device,
                ft.Container(height=10),
                txt_hotkey,
                dd_hotkey_mode,
                txt_speed
            ])
        )
    )

    # 3. Inference Settings Group
    
    # Online Provider Settings (Only visible when online mode)
    container_online = ft.Column([
        ft.Container(height=5),
        dd_provider,
        txt_api_key,
        dd_online_model,
        txt_custom_model_name,
        txt_api_base,
    ], visible=(raw_mode == "online"))

    # Local Model Settings Content (Only visible when local mode)
    container_local_content = ft.Column([
        ft.Text(t("local_model_settings"), size=18, weight="bold"),
        ft.Divider(),
        txt_timeout_label,
        cb_infinite,
        slider_timeout,
        ft.Container(height=10),
        dd_model,
        btn_convert,
        ft.Text(t("convert_help"), size=12, color="grey"),
        ft.Container(
            content=txt_console,
            bgcolor=ft.Colors.BLACK54,
            padding=10,
            border_radius=5,
        )
    ])

    card_local_settings = ft.Card(
        content=ft.Container(
            padding=15,
            content=container_local_content
        ),
        visible=(raw_mode == "local")
    )

    # Custom Model Settings (Only visible when custom mode)
    container_custom = ft.Column([
        ft.Text(t("custom_model"), size=18, weight="bold"),
        ft.Divider(),
        txt_custom_model,
        ft.Container(height=10),
        txt_timeout_label,
        cb_infinite,
        slider_timeout,
    ])

    card_custom_settings = ft.Card(
        content=ft.Container(
            padding=15,
            content=container_custom
        ),
        visible=(raw_mode == "custom")
    )

    def on_mode_change(e):
        mode = rg_mode.value
        container_online.visible = (mode == "online")
        card_local_settings.visible = (mode == "local")
        card_custom_settings.visible = (mode == "custom")
        page.update()

    rg_mode.on_change = on_mode_change

    card_inference = ft.Card(
        content=ft.Container(
            padding=15,
            content=ft.Column([
                ft.Text(t("inference_settings"), size=18, weight="bold"),
                rg_mode,
                cb_punctuation,
                container_online
            ])
        )
    )

    # AppBar - 保存ボタンを常に画面上部に固定
    page.appbar = ft.AppBar(
        title=ft.Text(t("title"), size=18),
        bgcolor=ft.Colors.SURFACE_CONTAINER,
        actions=[
            status_text,
            ft.Container(width=10),
            btn_save,
            ft.Container(width=10),
        ],
    )

    # Main Layout
    page.add(
        card_general,
        card_input,
        card_inference,
        card_local_settings,
        card_custom_settings,
        ft.Container(height=20),
    )

if __name__ == "__main__":
    ft.app(target=main)
