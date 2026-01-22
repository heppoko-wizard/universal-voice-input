
TRANSLATIONS = {
    "ja": {
        "title": "STT 設定エディタ",
        "api_settings": "基本設定",
        "groq_key": "Groq APIキー",
        "use_local": "ローカルモデルを使用する",
        "mic_device": "マイクデバイス",
        "hotkey": "グローバルホットキー",
        "speed_factor": "倍速調整 (例: 1.5)",
        "speed_hint": "1.0 = 標準, 2.0 = 2倍速",
        "local_model_settings": "ローカルモデル (最適化済み)",
        "model_path": "モデルのパス",
        "timeout_label": "モデル保持時間",
        "timeout_always": "常時保持 (最速)",
        "timeout_zero": "0秒 (即時解放 - メモリ節約)",
        "timeout_hybrid": "{s}秒 (ハイブリッド)",
        "always_loaded": "常時保持 (推奨)",
        "btn_convert": "ローカルモデルのセットアップ/更新",
        "btn_save": "保存して適用 (再起動)",
        "status_ready": "準備完了",
        "status_saving": "設定を保存中...",
        "status_saved": "保存完了。再起動しています...",
        "status_error": "エラー: {e}",
        "ui_language": "表示言語",
        "tray_settings": "設定",
        "tray_exit": "終了",
        "console_start": "変換を開始します...\n",
        "console_success": "\n成功: モデルが変換されました。",
        "console_failed": "\n失敗: 終了コード {code}",
        "console_error": "\nエラー: {error}"
    },
    "en": {
        "title": "STT Config Editor",
        "api_settings": "General Settings",
        "groq_key": "Groq API Key",
        "use_local": "Use Local Model",
        "mic_device": "Microphone Device",
        "hotkey": "Global Hotkey",
        "speed_factor": "Speed Up Factor (e.g. 1.5)",
        "speed_hint": "1.0 = Normal, 2.0 = Double Speed",
        "local_model_settings": "Local Model (Optimized)",
        "model_path": "Local Model Path",
        "timeout_label": "Model Keep Time",
        "timeout_always": "Always Loaded (Fastest)",
        "timeout_zero": "0s (Immediate Unload - Save Memory)",
        "timeout_hybrid": "{s}s (Hybrid)",
        "always_loaded": "Keep Loaded (Recommended)",
        "btn_convert": "Setup/Update Local Model",
        "btn_save": "Save & Apply (Restart)",
        "status_ready": "Ready.",
        "status_saving": "Saving settings...",
        "status_saved": "Settings Saved. Restarting...",
        "status_error": "Error: {e}",
        "ui_language": "UI Language",
        "tray_settings": "Settings",
        "tray_exit": "Exit",
        "console_start": "Starting conversion...\n",
        "console_success": "\nSUCCESS: Model converted.",
        "console_failed": "\nFAILED: Exit code {code}",
        "console_error": "\nError: {error}"
    },
    "zh": {
        "title": "STT 配置编辑器",
        "api_settings": "常规设置",
        "groq_key": "Groq API 密钥",
        "use_local": "使用本地模型",
        "mic_device": "麦克风设备",
        "hotkey": "全局快捷键",
        "speed_factor": "加速因子 (例如 1.5)",
        "speed_hint": "1.0 = 正常, 2.0 = 双倍速",
        "local_model_settings": "本地模型 (已优化)",
        "model_path": "本地模型路径",
        "timeout_label": "模型保留时间",
        "timeout_always": "始终保持 (最快)",
        "timeout_zero": "0秒 (立即释放 - 节省内存)",
        "timeout_hybrid": "{s}秒 (混合模式)",
        "always_loaded": "始终保持 (推荐)",
        "btn_convert": "设置/更新本地模型",
        "btn_save": "保存并应用 (重启)",
        "status_ready": "准备就绪",
        "status_saving": "正在保存设置...",
        "status_saved": "设置已保存。正在重启...",
        "status_error": "错误: {e}",
        "ui_language": "显示语言",
        "tray_settings": "设置",
        "tray_exit": "退出",
        "console_start": "开始转换...\n",
        "console_success": "\n成功：模型已转换。",
        "console_failed": "\n失败：退出代码 {code}",
        "console_error": "\n错误：{error}"
    }
}

def get_text(key, lang="ja", **kwargs):
    """
    指定された言語で文字列を返す。
    見つからない場合は日本語、それもなければキー自体を返す。
    """
    lang_map = TRANSLATIONS.get(lang, TRANSLATIONS["ja"])
    text = lang_map.get(key, TRANSLATIONS["ja"].get(key, key))
    
    if kwargs:
        try:
            return text.format(**kwargs)
        except:
            return text
    return text

def get_language_options():
    """ドロップダウン用の選択肢を返す"""
    return [
        {"key": "ja", "text": "日本語 (Japanese)"},
        {"key": "en", "text": "English"},
        {"key": "zh", "text": "简体中文 (Chinese)"}
    ]
