#!/usr/bin/env python3
"""
モデルのダウンロードと最適化を行うスクリプト。
引数でモデルIDを受け取るか、config.json から取得します。
"""
import os
import sys
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
    
    # 1. コマンドライン引数からモデルIDを取得（GUIから渡される）
    if len(sys.argv) > 1:
        model_id = sys.argv[1]
        logger.info(f"Model ID from argument: {model_id}")
    else:
        # フォールバック: config.jsonから読み取る
        if not os.path.exists(CONFIG_FILE):
            logger.error(f"{CONFIG_FILE} not found. Please run the GUI first.")
            return

        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        
        model_id = config.get("local_model_id", "RoachLin/kotoba-whisper-v2.2-faster")
        logger.info(f"Model ID from config: {model_id}")
    
    logger.info(f"Target Model: {model_id}")

    # 2. Local folder name (safe version of model_id)
    # models/kotoba-whisper-v2.2-faster のようにスラッシュ以降をフォルダ名にする
    model_name = model_id.split("/")[-1]
    output_dir = os.path.abspath(os.path.join(MODELS_DIR, model_name))
    
    logger.info(f"Setting up model in: {output_dir}")
    
    # 既存の入れ子になった古い形式などがあれば、ユーザーが混乱するため
    # 既存のフォルダがある場合はそのまま download_model に任せる（faster-whisperが適切に更新する）
    
    try:
        # download_model は CTranslate2 形式でダウンロード/キャッシュしてくれる
        # local_files_only=False で Hugging Face から取得
        # 指定した output_dir に直接展開されるようにする
        path = download_model(model_id, output_dir=output_dir)
        logger.info(f"Success! Model prepared at: {path}")
        
        print(f"\n[SUCCESS] Model '{model_name}' is ready.")
        
    except Exception as e:
        logger.error(f"Failed to setup model: {e}")
        exit(1)

if __name__ == "__main__":
    main()
