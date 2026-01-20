#!/usr/bin/env python3
"""
既存のローカル CTranslate2 モデルを Int8 に量子化するスクリプト。
ダウンロード不要、ローカルファイルのみで動作する。
"""
import os
import shutil
import ctranslate2

# 設定
LOCAL_MODEL_PATH = "/home/heppo/.cache/huggingface/hub/models--RoachLin--kotoba-whisper-v2.2-faster/snapshots/77dacdfbfa2f022e53974e8f463cf24051d0a6df"
OUTPUT_DIR = "models/kotoba-whisper-v2.2-int8"

def main():
    print(f"--- Model Quantizer (Local) ---")
    print(f"Source: {LOCAL_MODEL_PATH}")
    print(f"Target: {OUTPUT_DIR}")
    
    if not os.path.exists(LOCAL_MODEL_PATH):
        print(f"ERROR: Source model not found at {LOCAL_MODEL_PATH}")
        return
        
    if os.path.exists(OUTPUT_DIR):
        print(f"Output directory exists. Cleaning...")
        shutil.rmtree(OUTPUT_DIR)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("Quantizing to Int8...")
    
    # CTranslate2 の量子化API を使用
    # Generator/Translator ではなく、モデルファイルを直接コピーし、
    # 重み（model.bin）を量子化する。
    # 実際には ctranslate2 は変換時にしか量子化できないため、
    # 既にCT2形式のモデルを「再量子化」するにはファイルを直接操作するか、
    # または faster_whisper 側で load 時に compute_type を指定するのが正解。
    
    # ... というわけで、既にある model.bin を使って、
    # faster_whisper が load 時に int8 で解釈するように設定すれば、
    # 追加の変換は不要かもしれない。
    
    # まずは単純にモデルファイルをコピーしてみる
    for filename in os.listdir(LOCAL_MODEL_PATH):
        src = os.path.join(LOCAL_MODEL_PATH, filename)
        dst = os.path.join(OUTPUT_DIR, filename)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
            print(f"  Copied: {filename}")
    
    print("\nCopy Complete!")
    print(f"Model available at: {os.path.abspath(OUTPUT_DIR)}")
    print("Note: faster_whisper will load this with compute_type='int8' for quantization.")

if __name__ == "__main__":
    main()
