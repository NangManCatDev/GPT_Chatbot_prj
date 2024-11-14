import os
import requests
import urllib.parse
import wave
import winsound
import pyaudio
import threading
from dotenv import load_dotenv

load_dotenv()

p = pyaudio.PyAudio()

devices = p.get_device_count()
for i in range(devices):
    device_info = p.get_device_info_by_index(i)
    if device_info.get('maxInputChannels') > 0:
        print(f"입력: {device_info.get('name')} , Device Index: {device_info.get('index')}")
    else:
        print(f"출력: {device_info.get('name')} , Device Index: {device_info.get('index')}")

base_url = 'http://localhost:50021'

def play_with_pyaudio(speech_filename):
    p = pyaudio.PyAudio()
    wav_file = wave.open(speech_filename, 'rb')
    stream = p.open(format=p.get_format_from_width(wav_file.getsampwidth()),
                    channels=wav_file.getnchannels(),
                    rate=wav_file.getframerate(),
                    output_device_index=5,
                    output=True)

    data = wav_file.readframes(1024)
    while data:
        stream.write(data)
        data = wav_file.readframes(1024)

    stream.stop_stream()
    stream.close()
    wav_file.close()
    p.terminate()

def speak_with_voicevox(text):
    speaker_id = '8'
    
    # 8, 10, 14, 20, 54, 61, 66, 69
    # 80번까지 확인해봤음

    params_encoded = urllib.parse.urlencode({'text': text, 'speaker': speaker_id})
    req = requests.post(f'{base_url}/audio_query?{params_encoded}')
    req.raise_for_status()

    query = req.json()

    query['volumeScale'] = 1.00
    query['intonationScale'] = 1.00
    query['prePhonemeLength'] = 0.10
    query['postPhonemeLength'] = 0.10
    query['speedScale'] = 1
    query['pitchScale'] = 0
    query['pitchScale'] = 0

    params_encoded = urllib.parse.urlencode({'speaker': speaker_id})
    req = requests.post(f'{base_url}/synthesis?{params_encoded}', json=query)
    req.raise_for_status()

    speech_filename = 'speech.wav'
    with open(speech_filename, 'wb') as outfile:
        outfile.write(req.content)

    pyaudio_thread = threading.Thread(target=play_with_pyaudio, args=(speech_filename,))
    pyaudio_thread.start()

    winsound.PlaySound(speech_filename, winsound.SND_FILENAME)

    pyaudio_thread.join()

# Example usage
msg = "ある日、犬がアイスクリーム屋さんに入ってきました。"
# msg = "はじめまして、なんまんごやんいさんの, パーソナルアシスタント, メガミちゃんです。"
speak_with_voicevox(msg)
