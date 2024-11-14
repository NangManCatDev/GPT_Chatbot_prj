import os
import requests
import urllib.parse
import winsound
from dotenv import load_dotenv

load_dotenv()

# Set the base URL for the Voicevox API
base_url = 'http://localhost:50021'

# Function to convert text to speech using VoiceVox and play it
def speak_with_voicevox(text):
    # Set the speaker ID for the VoiceVox character
    speaker_id = '20'  # 원하는 캐릭터의 ID로 설정 (이 예시에서는 ID 5번)
    
    # 8, 10, 14, 20, 54, 61, 66, 69
    # 80번까지 확인해봤음

    # Create the query for VoiceVox API
    params_encoded = urllib.parse.urlencode({'text': text, 'speaker': speaker_id})
    req = requests.post(f'{base_url}/audio_query?{params_encoded}')
    req.raise_for_status()  # 요청 실패 시 에러 발생

    # Get the query response
    query = req.json()
    
    # Optional: Modify query parameters like volume, intonation, etc.
    query['volumeScale'] = 1.00  # 音量 (음량)
    query['intonationScale'] = 1.00  # 抑揚 (억양)
    query['prePhonemeLength'] = 0.10  # 開始無音 (시작 무음)
    query['postPhonemeLength'] = 0.10  # 終了無音 (종료 무음)

    # Synthesize the voice
    params_encoded = urllib.parse.urlencode({'speaker': speaker_id})
    req = requests.post(f'{base_url}/synthesis?{params_encoded}', json=query)
    req.raise_for_status()  # 요청 실패 시 에러 발생

    # Save the synthesized voice to a file
    speech_filename = 'speech.wav'
    with open(speech_filename, 'wb') as outfile:
        outfile.write(req.content)

    # Play the synthesized voice
    winsound.PlaySound(speech_filename, winsound.SND_FILENAME)

# Example usage of the speak_with_voicevox function with the msg variable
# msg = "これはテストメッセージです。"  # This is the Japanese text you want to convert to speech
# msg = "はじめまして、なんまんごやんいさんの, パーソナルアシスタント, メガミちゃんです。"
# speak_with_voicevox(msg)
