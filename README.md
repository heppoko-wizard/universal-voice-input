# Open STT Tool

**ホットキー一発で、アクティブなウィンドウに声を直接入力するデスクトップアプリ。**

[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-blue)](https://github.com)
[![Python](https://img.shields.io/badge/python-3.10%2B-brightgreen)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-orange)](LICENSE)

---

グローバルホットキーを押して話すだけで、ブラウザ・エディタ・チャットアプリ等のカーソル位置へ文字を自動入力します。  
ローカルAIモデルによって、**音声データをインターネット上に送らず**高速に文字起こしが完結します。

---

## 目次 / Table of Contents

- [機能](#機能-features)
- [動作要件](#動作要件-requirements)
- [インストール](#インストール-installation)
- [使い方](#使い方-usage)
- [設定項目](#設定項目-configuration)
- [技術スタック](#技術スタック-tech-stack)
- [License](#license)

---

## 機能 / Features

- **キーボードレスで入力** — ホットキーを押して話すだけで、現在アクティブなウィンドウのカーソル位置にそのままテキストが入力される
- **完全ローカル処理（プライバシー保護）** — `faster-whisper` エンジンにより音声データは端末の外に出ない。社外秘・個人情報の入力に安心して使える
- **GPUのない環境でも使える** — ローカル推論が難しいスペックの場合、Groq / OpenAI 等のクラウドAPIへワンクリックで切り替え可能
- **録音モードを選べる** — トグル（押して開始/もう一度押して終了）とホールド（押している間だけ録音）の2スタイル
- **VRAMをゲームや他アプリと共有できる** — 「使わない時間はモデルを自動でメモリから解放する」設定で、他の用途に影響を与えない
- **GUIで全設定が完結** — マイクデバイス・ホットキー・AIモデルの変更はすべてGUI操作で行える（設定ファイルの直接編集不要）

---

## 動作要件 / Requirements

| 項目 | 最低要件 |
|------|---------|
| OS | Windows 10+ / macOS 12+ / Linux (X11 or Wayland) |
| Python | 3.10 以上 |
| GPU | CUDA対応GPU推奨（ローカルモード時）。なくてもオンラインモードで動作 |
| マイク | OSが認識するUSBマイク・内蔵マイクなど |

---

## インストール / Installation

最も簡単な方法は、[Releases](https://github.com/your-username/open-stt-tool/releases) ページから最新の ZIP ファイルをダウンロードすることです。

1. [Releases](https://github.com/your-username/open-stt-tool/releases) から最新の `open-stt-tool-vX.X.X.zip` をダウンロード
2. 任意のフォルダに解凍
3. フォルダ内の各 OS 向けセットアップスクリプトを実行：
   - **Windows**: `setup_windows.ps1` を右クリックして「PowerShell で実行」
   - **macOS / Linux**: ターミナルで `bash setup_macos.sh` または `bash setup_linux.sh` を実行

---

### 開発者向け (Manual Install)
ソースコードを取得してインストールする場合：

### Linux
```bash
git clone https://github.com/your-username/open-stt-tool.git
cd open-stt-tool
bash setup_linux.sh
```

### macOS
```bash
git clone https://github.com/your-username/open-stt-tool.git
cd open-stt-tool
bash setup_macos.sh
```

### Windows
```powershell
git clone https://github.com/your-username/open-stt-tool.git
cd open-stt-tool
.\setup_windows.ps1
```

セットアップ完了後、デスクトップに **Open STT Tool** ショートカットが作成されます。

---

## 使い方 / Usage

1. **起動**: デスクトップのショートカットをダブルクリック（またはシステムトレイのアイコンから操作）
2. **録音開始**: デフォルトの `Ctrl+Shift+Space` を押して話す
3. **録音終了**: 同じキーをもう一度押す（トグルモード）
4. 自動的に文字起こしされ、アクティブなウィンドウへ入力されます

> 設定変更はシステムトレイアイコンを右クリック →「設定を開く」から。

---

## 設定項目 / Configuration

| 設定 | 説明 |
|------|------|
| `hotkey` | グローバルホットキー（デフォルト: `<ctrl>+<shift>+<space>`） |
| `hotkey_mode` | `toggle`（押して開始/停止）or `hold`（長押し中のみ録音） |
| `model_mode` | `local`（ローカル）/ `online`（クラウドAPI）/ `custom`（カスタムパス） |
| `local_model_id` | 使用するWhisperモデルID |
| `local_model_timeout` | アイドル後のモデル解放時間（秒）。`-1` で常時保持 |
| `ui_position` | フローティングバーの表示位置（`top` / `center` / `bottom`） |
| `ui_language` | GUIの表示言語（`ja` / `en` / `zh`） |

設定ファイルは `config.json`（プロジェクトルート）に保存されます。GUIから変更した場合も自動でこのファイルに反映されます。

---

## 技術スタック / Tech Stack

| カテゴリ | ライブラリ |
|----------|-----------|
| 音声文字起こし | `faster-whisper` |
| クラウドAPI連携 | `litellm` (Groq, OpenAI 等) |
| GUI | `Flet` |
| システムトレイ | `pystray` |
| グローバルホットキー | `pynput` |
| オーディオキャプチャ | `sounddevice` |
| クリップボード制御 | `pyperclip` |

---

## License

MIT License — 詳細は [LICENSE](LICENSE) を参照してください。

---

---

# Open STT Tool (English)

**Dictate into any active window with a global hotkey. No mouse, no clipboard — just talk and type.**

Press your hotkey, speak, and your words appear directly at the cursor in whichever app is active (browser, editor, chat, etc.).  
A local AI model handles all transcription **on-device**, so no audio ever leaves your machine.

---

## Features

- **Truly hands-free input** — Press a hotkey, talk, release. Text appears at the cursor in any app
- **Private by default** — All processing happens locally via `faster-whisper`. Audio never sent to the cloud
- **Works without a GPU** — Swap to Groq or OpenAI cloud API in one click if local inference is too slow on your machine
- **Choose your recording style** — Toggle mode (press to start/stop) or Hold mode (record only while pressing)
- **VRAM-friendly** — Configure the model to auto-unload after a period of inactivity, freeing memory for games or other workloads
- **Everything configurable via GUI** — Change mic, hotkey, and AI model without editing any config files

---

## Requirements

| Item | Requirement |
|------|-------------|
| OS | Windows 10+ / macOS 12+ / Linux (X11 or Wayland) |
| Python | 3.10+ |
| GPU | CUDA GPU recommended for local mode. Not required with online mode |
| Microphone | Any OS-recognized USB/built-in microphone |

---

## Installation

The easiest way is to download the latest ZIP from the [Releases](https://github.com/your-username/open-stt-tool/releases) page.

1. Download `open-stt-tool-vX.X.X.zip` from [Releases](https://github.com/your-username/open-stt-tool/releases).
2. Extract the ZIP to any folder.
3. Run the setup script for your OS:
   - **Windows**: Right-click `setup_windows.ps1` and select "Run with PowerShell".
   - **macOS / Linux**: Run `bash setup_macos.sh` or `bash setup_linux.sh` in your terminal.

---

### For Developers (Manual Install)
If you prefer to clone the repository:

### Linux
```bash
git clone https://github.com/your-username/open-stt-tool.git
cd open-stt-tool
bash setup_linux.sh
```

### macOS
```bash
git clone https://github.com/your-username/open-stt-tool.git
cd open-stt-tool
bash setup_macos.sh
```

### Windows
```powershell
git clone https://github.com/your-username/open-stt-tool.git
cd open-stt-tool
.\setup_windows.ps1
```

A desktop shortcut will be created automatically on setup.

---

## Usage

1. **Launch**: Double-click the desktop shortcut or start from the system tray
2. **Start**: Press `Ctrl+Shift+Space` (default) and speak
3. **Stop**: Press the hotkey again (toggle mode)
4. The transcription is automatically typed into the active window

> To change settings, right-click the system tray icon → "Open Settings".

---

## Configuration

| Key | Description |
|-----|-------------|
| `hotkey` | Global hotkey (default: `<ctrl>+<shift>+<space>`) |
| `hotkey_mode` | `toggle` or `hold` |
| `model_mode` | `local` / `online` / `custom` |
| `local_model_id` | Whisper model ID to use |
| `local_model_timeout` | Seconds before unloading model. `-1` = always loaded |
| `ui_position` | Floating bar position: `top` / `center` / `bottom` |
| `ui_language` | Interface language: `ja` / `en` / `zh` |

Config is stored in `config.json` at the project root. The GUI writes to this file automatically.

---

## Tech Stack

| Category | Library |
|----------|---------|
| Transcription | `faster-whisper` |
| Cloud API | `litellm` (Groq, OpenAI, etc.) |
| GUI | `Flet` |
| System tray | `pystray` |
| Global hotkey | `pynput` |
| Audio capture | `sounddevice` |
| Clipboard | `pyperclip` |

---

## License

MIT License — see [LICENSE](LICENSE) for details.
