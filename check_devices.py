import sounddevice as sd

def list_audio_devices():
    print("--- Audio Devices (sounddevice) ---")
    devices = sd.query_devices()
    print(devices)

    print("\n--- Input Devices ---")
    for i, dev in enumerate(devices):
        if dev['max_input_channels'] > 0:
            print(f"Index {i}: {dev['name']} (Channels: {dev['max_input_channels']})")

if __name__ == "__main__":
    list_audio_devices()
