# SudachiPy Punctuation Restoration Implementation Plan

## Goal Description

Whisper's internal punctuation can be unreliable. We will implement a post-processing step using SudachiPy to analyze the transcribed text and insert "、" and "。" based on grammatical rules (POS tags).

## User Review Required
>
> [!NOTE]
> This is a rule-based approach. It will detect typical sentence endings (です, ます, だ, 等) and insert "。" if missing. It will also look for major conjunctions to insert "、".

## Proposed Changes

### Core Logic

#### [NEW] [punctuation_utils.py](file:///home/heppo/ai_tools/speech_to_text/punctuation_utils.py)

Create a utility to:

- Initialize SudachiPy tokenizer.
- Provide a `restore_punctuation(text)` function.
- Identify sentence endings via POS tags and add "。".
- Identify conjunctions/pauses and add "、".

### STT Workers

#### [MODIFY] [stt_worker.py](file:///home/heppo/ai_tools/speech_to_text/stt_worker.py)

#### [MODIFY] [stt_worker_persistent.py](file:///home/heppo/ai_tools/speech_to_text/stt_worker_persistent.py)

- Import `punctuation_utils`.
- Call `restore_punctuation` on the final transcribed text if the option is enabled.
- Remove `initial_prompt` hacks that weren't effective.

### Configuration

- Keep the existing `add_punctuation` toggle in `config.json`.

## Verification Plan

### Automated Tests

- Create a script to test `punctuation_utils.py` with sample texts (e.g., "こんにちは元気です今日はいい天気ですね").
- Verify that "こんにちは、元気です。今日はいい天気ですね。" (or similar) is returned.
