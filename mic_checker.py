#!/usr/bin/env python3
"""
Mic Checker - マイクの生存確認モジュール
短時間録音してRMS値を計算し、デバイスが音を拾っているか判定する。
疎結合設計：他モジュールからワンコールで使用可能。
"""
import logging
import numpy as np
import sounddevice as sd

logger = logging.getLogger("MicChecker")

def check_device(device_index, duration=0.5, sample_rate=44100, threshold=0.0001):
    """
    指定デバイスで短時間録音し、生存確認する。
    
    Args:
        device_index: デバイスインデックス (None=システムデフォルト)
        duration: 録音時間（秒）
        sample_rate: サンプルレート
        threshold: RMS閾値（これ以上なら alive）
    
    Returns:
        {"alive": bool, "rms": float, "error": str|None, "device_name": str}
    """
    try:
        # デバイス名を取得
        if device_index is not None:
            dev_info = sd.query_devices(device_index)
            device_name = dev_info['name']
        else:
            device_name = "System Default"
        
        # 短時間録音
        audio = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            device=device_index,
            dtype='float32'
        )
        sd.wait()
        
        # RMS計算
        rms = float(np.sqrt(np.mean(audio ** 2)))
        alive = rms > threshold
        
        logger.info(f"Device {device_index} ({device_name}): RMS={rms:.6f}, alive={alive}")
        
        return {
            "alive": alive,
            "rms": rms,
            "error": None,
            "device_name": device_name
        }
        
    except Exception as e:
        logger.warning(f"Device {device_index} check failed: {e}")
        return {
            "alive": False,
            "rms": 0.0,
            "error": str(e),
            "device_name": f"Device {device_index}"
        }


def get_input_device_indices():
    """入力チャンネルを持つデバイスのインデックス一覧を返す"""
    indices = []
    try:
        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            if dev['max_input_channels'] > 0:
                indices.append(i)
    except Exception as e:
        logger.error(f"Failed to enumerate devices: {e}")
    return indices


def find_working_device(preferred_index=None, sample_rate=44100):
    """
    動作するマイクデバイスを探す。
    
    1. preferred_index をチェック
    2. ダメなら全入力デバイスをスキャン
    3. 音を拾っているデバイスに切り替え
    
    Args:
        preferred_index: 優先デバイスのインデックス (None=指定なし)
        sample_rate: サンプルレート
    
    Returns:
        {
            "device_index": int|None,  # 使用すべきデバイス (Noneは全滅)
            "device_name": str,        # デバイス名
            "fallback": bool,          # フォールバックが発生したか
            "preferred_name": str,     # 元の優先デバイス名
            "message": str             # 状態メッセージ
        }
    """
    result = {
        "device_index": None,
        "device_name": "",
        "fallback": False,
        "preferred_name": "",
        "message": ""
    }
    
    # 1. 優先デバイスをチェック
    if preferred_index is not None:
        check = check_device(preferred_index, sample_rate=sample_rate)
        result["preferred_name"] = check["device_name"]
        
        if check["alive"]:
            result["device_index"] = preferred_index
            result["device_name"] = check["device_name"]
            result["message"] = f"Default device OK: {check['device_name']} (RMS={check['rms']:.6f})"
            logger.info(result["message"])
            return result
        else:
            logger.warning(f"Preferred device {preferred_index} ({check['device_name']}) is silent or failed: {check.get('error', 'no signal')}")
    
    # 2. 全入力デバイスをスキャン
    logger.info("Scanning all input devices...")
    all_devices = get_input_device_indices()
    
    for idx in all_devices:
        if idx == preferred_index:
            continue  # 既にチェック済み
        
        check = check_device(idx, sample_rate=sample_rate)
        if check["alive"]:
            result["device_index"] = idx
            result["device_name"] = check["device_name"]
            result["fallback"] = True
            result["message"] = f"Fallback to device {idx}: {check['device_name']} (RMS={check['rms']:.6f})"
            logger.info(result["message"])
            return result
    
    # 3. 全滅
    result["message"] = "No working microphone found"
    logger.error(result["message"])
    return result


if __name__ == "__main__":
    # スタンドアロンテスト
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')
    
    print("=== Mic Checker Test ===")
    print(f"Input devices: {get_input_device_indices()}")
    
    result = find_working_device()
    print(f"\nResult: {result}")
