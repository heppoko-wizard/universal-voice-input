# Punctuation Option Implementation Plan

## Goal Description

Add a user-selectable option to enable or disable automatic punctuation (、。) in the generated text. While Kotoba-Whisper supports punctuation, providing an explicit toggle and using prompts helps ensure consistency for users who want it.

## User Review Required
>
> [!NOTE]
> Punctuation will be encouraged by providing an initial prompt ("こんにちは、元気ですか。") to the model and enabling context-aware transcription.

## Proposed Changes

### Configuration

#### [MODIFY] [config_manager.py](file:///home/heppo/ai_tools/speech_to_text/config_manager.py)

- Add `"add_punctuation": True` to `DEFAULT_CONFIG`.

### GUI

#### [MODIFY] [gui.py](file:///home/heppo/ai_tools/speech_to_text/gui.py)

- Add a checkbox for "Automatic Punctuation" (`cb_punctuation`).
- Update the save logic to store this setting in `config.json`.

### STT Workers

#### [MODIFY] [stt_worker.py](file:///home/heppo/ai_tools/speech_to_text/stt_worker.py)

#### [MODIFY] [stt_worker_persistent.py](file:///home/heppo/ai_tools/speech_to_text/stt_worker_persistent.py)

- Retrieve `add_punctuation` from the config.
- Update the `model.transcribe` call to include `initial_prompt` and `condition_on_previous_text` when enabled.

## Verification Plan

### Automated Tests

- Restart the GUI and verify the checkbox state persists after saving.
- Check the `config.json` file for the `add_punctuation` key.
- (Manual) Run a transcription and verify if punctuation is present.
