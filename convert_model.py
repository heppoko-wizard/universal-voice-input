#!/usr/bin/env python3
"""
モデルのダウンロードと最適化を行うスクリプト。
config.json で指定されたモデル ID を取得し、models/ フォルダ以下に準備します。
"""
import os
import shutil
import json
import logging
from faster_whisper import download_model

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [CONVERT] %(message)s')
logger = logging.getLogger("Converter")

CONFIG_FILE = "config.json"
MODELS_DIR = "models"

def main():
    logger.info("--- Model Setup / Update ---")
    
    # 1. Load Config
    if not os.path.exists(CONFIG_FILE):
        logger.error(f"{CONFIG_FILE} not found. Please run the GUI first.")
        return

    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
    
    model_id = config.get("local_model_id", "RoachLin/kotoba-whisper-v2.2-faster")
    logger.info(f"Target Model: {model_id}")

    # 2. Local folder name (safe version of model_id)
    # models/kotoba-whisper-v2.2-faster のようにスラッシュ以降をフォルダ名にする
    model_name = model_id.split("/")[-1]
    output_dir = os.path.join(MODELS_DIR, model_name)
    
    # すでに変換済みのInt8版があるか、などの判定は複雑なので、
    # シンプルに毎回 download_model を通す（あれば高速に終わる）
    logger.info(f"Setting up model in: {output_dir}")
    
    try:
        # download_model は CTranslate2 形式でダウンロード/キャッシュしてくれる
        # local_files_only=False で Hugging Face から取得
        path = download_model(model_id, output_dir=output_dir)
        logger.info(f"Success! Model prepared at: {path}")
        
        # models/ 以下を Worker が見つけやすいように、config の local_model_size (パス用) を更新する
        # ※ stt_worker_unified.py 側で解決する方が綺麗だが、一旦ここで完了報告
        print(f"\n[SUCCESS] Model '{model_name}' is ready.")
        
    except Exception as e:
        logger.error(f"Failed to setup model: {e}")
        exit(1)

if __name__ == "__main__":
    main()
