#!/usr/bin/env python3
"""
Mic Checker - マイクの生存確認モジュール（簡易版）
設定されたデバイスで短時間録音し、完全無音なら警告通知を出す。
config の書き換えは一切行わない。
"""
import logging
import numpy as np
import sounddevice as sd

logger = logging.getLogger("MicChecker")

# 完全無音の判定閾値（RMS）
SILENCE_THRESHOLD = 0.0001


def check_device(device_index, sample_rate=44100, duration=0.5):
    """
    指定デバイスで短時間録音し、無音かどうかを返す。
    デバイスの max_input_channels に合わせてチャンネル数を自動選択する。
    
    Returns:
        {"silent": bool, "rms": float, "error": str|None, "device_name": str}
    """
    try:
        # デバイス情報取得
        if device_index is not None:
            dev_info = sd.query_devices(device_index)
            device_name = dev_info['name']
            channels = min(dev_info['max_input_channels'], 2)  # 最大2ch
        else:
            device_name = "System Default"
            channels = 1

        # 短時間録音
        audio = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=channels,
            device=device_index,
            dtype='float32'
        )
        sd.wait()

        # ステレオの場合はモノラルに変換してRMS計算
        if audio.ndim > 1 and audio.shape[1] > 1:
            audio = audio.mean(axis=1)

        rms = float(np.sqrt(np.mean(audio ** 2)))
        silent = rms < SILENCE_THRESHOLD

        logger.info(f"Device {device_index} ({device_name}): RMS={rms:.6f}, silent={silent}")

        return {
            "silent": silent,
            "rms": rms,
            "error": None,
            "device_name": device_name
        }

    except Exception as e:
        logger.warning(f"Device {device_index} check failed: {e}")
        return {
            "silent": True,
            "rms": 0.0,
            "error": str(e),
            "device_name": f"Device {device_index}"
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')
    
    print("=== Mic Checker Test ===")
    result = check_device(None)
    print(f"Result: {result}")
