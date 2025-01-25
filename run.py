import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
import requests
import urllib.parse
import wave
import winsound
import sys
import pyaudio
import threading
import logging
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

logging.getLogger("langchain").setLevel(logging.ERROR)

# to help the CLI write unicode characters to the terminal
sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf8", buffering=1)

base_url = "http://localhost:50021"


def load_system_prompt(filepath):
    with open(filepath, "r", encoding="utf-8") as file:
        return file.read()


# 파일 경로 설정 (필요 시 절대 경로나 환경 변수 사용)
system_prompt_path = "System_prompt.txt"

# system 프롬프트 로드
system_prompt = load_system_prompt(system_prompt_path)


def play_with_pyaudio(speech_filename):
    p = pyaudio.PyAudio()
    wav_file = wave.open(speech_filename, "rb")
    stream = p.open(
        format=p.get_format_from_width(wav_file.getsampwidth()),
        channels=wav_file.getnchannels(),
        rate=wav_file.getframerate(),
        output_device_index=6,
        output=True,
    )

    data = wav_file.readframes(1024)
    while data:
        stream.write(data)
        data = wav_file.readframes(1024)

    stream.stop_stream()
    stream.close()
    wav_file.close()
    p.terminate()


def speak_with_voicevox(text):
    speaker_id = "8"

    params_encoded = urllib.parse.urlencode({"text": text, "speaker": speaker_id})
    req = requests.post(f"{base_url}/audio_query?{params_encoded}")
    req.raise_for_status()

    query = req.json()
    query["volumeScale"] = 1.00
    query["intonationScale"] = 0.60
    query["prePhonemeLength"] = 0.10
    query["postPhonemeLength"] = 0.10

    params_encoded = urllib.parse.urlencode({"speaker": speaker_id})
    req = requests.post(f"{base_url}/synthesis?{params_encoded}", json=query)
    req.raise_for_status()

    speech_filename = "speech.wav"
    with open(speech_filename, "wb") as outfile:
        outfile.write(req.content)

    return speech_filename  # 파일 이름을 반환


def speak_and_play(text):
    # 음성 파일 생성
    speech_filename = speak_with_voicevox(text)

    if speech_filename and os.path.exists(speech_filename):
        # PyAudio를 사용하여 파일 재생
        pyaudio_thread = threading.Thread(
            target=play_with_pyaudio, args=(speech_filename,)
        )
        pyaudio_thread.start()

        # Winsound를 사용하여 재생을 별도의 스레드에서 실행
        winsound_thread = threading.Thread(
            target=winsound.PlaySound, args=(speech_filename, winsound.SND_FILENAME)
        )
        winsound_thread.start()

        # 두 스레드가 종료될 때까지 대기
        pyaudio_thread.join()
        winsound_thread.join()
    else:
        print(f"Error: 음성 파일을 찾을 수 없습니다. 파일 이름: {speech_filename}")


# OpenAI API 키 설정
api_key = os.environ["OPENAI_API_KEY"]

# 세션 기록을 관리할 변수 (직접 관리)
session_store = {}


# 세션 기록을 가져오는 함수
def get_session_history(session_id: str):
    if session_id not in session_store:
        session_store[session_id] = ChatMessageHistory()
    return session_store[session_id]


# response를 생성하는 함수
def generate_response(user_input: str, session_id: str):
    llm = ChatOpenAI(openai_api_key=api_key, model_name="gpt-4", temperature=1)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),  # 외부 파일에서 불러온 system 프롬프트 사용
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ]
    )

    chain = prompt | llm  # 프롬프트를 llm에 넣어 chain 구성

    chain_with_memory = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="question",
        history_messages_key="history",
    )

    response = chain_with_memory.invoke(
        {"question": user_input},
        config={"configurable": {"session_id": session_id}},
    )

    return response.content


def chat():
    print("メガミ: hello!")
    session_id = "unique_session_id"
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["종료", "exit", "quit"]:
            print("メガミ: 안녕히 가세요!")
            speak_with_voicevox(f"さようなら")
            break

        response = generate_response(user_input, session_id)
        print(f"メガミ: {response}")

        # 음성 합성 및 재생을 위한 스레드 생성
        tts_thread = threading.Thread(target=speak_and_play, args=(response,))
        tts_thread.start()
        tts_thread.join()  # 재생이 완료될 때까지 대기


if __name__ == "__main__":
    chat()
