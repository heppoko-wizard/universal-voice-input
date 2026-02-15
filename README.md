# Cross-Platform AI Speech-to-Text Tool

A high-performance speech-to-text tool for Linux, macOS, and Windows. This tool supports both local inference using Faster-Whisper and cloud-based transcription via Groq/OpenAI APIs.

## Key Features

1. Advanced Notification Control
The application now supports finer control over the notification area. Notifications remain visible during the entire recording process to provide clear status feedback.

2. Flexible Model Management
The tool provides four distinct operation modes to balance performance and resource usage:

- Local Load: Loads the model only when needed.
- CPU Offload: Offloads processing to the CPU to save VRAM for other tasks like gaming or image generation.
- Timed VRAM Retention: Keeps the model in VRAM for a specified number of seconds after transcription, then automatically unloads it.
- Resident VRAM: Keeps the model permanently in VRAM for immediate response in subsequent transcriptions.

1. GUI Enhancements
The settings GUI has been updated to allow easy selection between the four model management modes and configuration of notification behaviors.

2. Performance Optimization
Utilizes GPU acceleration (CUDA) with support for local model loading to ensure low latency and high accuracy for Japanese and English transcription.

## Requirements

- Python 3.10 or higher
- FFmpeg
- NVIDIA GPU with CUDA Toolkit 12+ (Optional, for GPU acceleration)

---

# クロスプラットフォーム AI 音声認識ツール

Linux, macOS, Windows で動作する高性能な音声認識ツールです。Faster-Whisper によるローカル推論と、Groq/OpenAI API を使用したクラウド推論の両方に対応しています。

## 主な機能

1. 高度な通知制御
通知領域の制御が可能になりました。録音中は通知が消えることなく表示され続け、現在のステータスを確実に把握できます。

2. 柔軟なモデル管理
パフォーマンスとリソース使用量のバランスを調整するため、以下の4つの動作モードを提供します：

- ローカル読み込み: 必要時にのみモデルを読み込みます。
- CPUオフロード: 処理をCPUにオフロードし、ゲームや画像生成などのためにVRAMを節約します。
- タイマー式VRAM保持: 文字起こし終了後、指定した秒数だけモデルをVRAMに保持し、その後自動的に破棄します。
- VRAM常駐: モデルを常にVRAMに保持し、次回の文字起こしで即座に反応できるようにします。

1. GUI の改善
設定 GUI が更新され、4つのモデル管理モードの選択や通知挙動の設定が容易に行えるようになりました。

2. パフォーマンスの最適化
GPU アクセラレーション（CUDA）を活用し、ローカルモデルの読み込みに対応することで、日本語および英語の文字起こしにおいて低遅延かつ高精度な認識を実現しています。

## 必要条件

- Python 3.10 以上
- FFmpeg
- NVIDIA GPU and CUDA Toolkit 12+ (Optional, for GPU acceleration)

## Installation & Usage

### Windows
1. Right-click `setup_windows.ps1` and select "Run with PowerShell".
2. Wait for the setup to complete.
3. A shortcut **"Open-STT-Tool"** will be created on your Desktop.
4. Double-click the shortcut to start the tool.

### macOS
1. Open Terminal and navigate to the folder.
2. Run `sh setup_macos.sh`.
3. A file **`start_stt_gui.command`** will be created in the folder.
4. Double-click `start_stt_gui.command` to start.

### Linux
1. Run `sh setup_linux.sh`.
2. Use `./start_stt.sh` or the created desktop shortcut.

---

## 必要条件

- Python 3.10 以上
- FFmpeg
- NVIDIA GPU および CUDA Toolkit 12以上（任意、GPU加速を利用する場合）

## インストールと使い方

### Windows
1. `setup_windows.ps1` を右クリックし、「PowerShellで実行」を選択します。
2. セットアップが完了するのを待ちます。
3. デスクトップに **「Open-STT-Tool」** というショートカットが作成されます。
4. これをダブルクリックして起動します。

### macOS
1. ターミナルを開き、フォルダに移動します。
2. `sh setup_macos.sh` を実行します。
3. フォルダ内に **`start_stt_gui.command`** というファイルが作成されます。
4. これをダブルクリックして起動します。

### Linux
1. `sh setup_linux.sh` を実行します。
2. `./start_stt.sh` または作成されたデスクトップショートカットを使用します。
