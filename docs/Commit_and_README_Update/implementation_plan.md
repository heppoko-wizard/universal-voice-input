# Commit and Documentation Update Plan

## Goal Description

Current changes in the STT system need to be documented in `README.md` (bilingual, no emojis) and committed with a specific message detailing the new features (notification control, VRAM modes, etc.).

## Proposed Changes

### Documentation

#### [MODIFY] [README.md](file:///home/heppo/ai_tools/speech_to_text/README.md)

Update the content to include both English and Japanese descriptions, removing all emojis as requested. Focus on the following new features:

- Notification management enhancements (recording persistence, control support).
- Operations modes for VRAM/Processor:
  - Local Loading
  - CPU Offload
  - VRAM Retention (Unload after specific duration)
  - VRAM Resident (Keep loaded)
- GUI updates for mode selection.

### Version Control

- Execute `git add .` to stage all changes.
- Execute `git commit` with the following message (en/jp content as requested):
  - English: "Added notification area control, persistent notifications during recording, local model loading, CPU offload support, and a GUI for choosing between 4 VRAM management modes (Local, CPU Offload, Timed VRAM Retention, Resident VRAM)."
  - Japanese: "通知領域の制御機能を追加、録音中の通知固定化、モデルのローカル読み込み、CPUオフロード対応、および4つのモデル管理モード（ローカル、CPUオフロード、タイマー式VRAM保持、VRAM常駐）を選択可能なGUIを実装しました。"

## Verification Plan

### Automated Tests

- Check if `README.md` exists and contains the expected content.
- Verify git history for the new commit.
