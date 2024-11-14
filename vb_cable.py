import pyaudio
import wave
import subprocess

p = pyaudio.PyAudio()

devices = p.get_device_count()
# Iterate through all devices
for i in range(devices):
    # Get the device info
    device_info = p.get_device_info_by_index(i)
    # Check if this device is a microphone (an input device)
    if device_info.get('maxInputChannels') > 0:
        print(f"입력: {device_info.get('name')} , Device Index: {device_info.get('index')}")
    else:
        print(f"출력: {device_info.get('name')} , Device Index: {device_info.get('index')}")