import os
import threading
from datetime import datetime
from functools import lru_cache
from pytz import timezone
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from dateutil import parser
from Google_Calendar import get_upcoming_events
from dotenv import load_dotenv
import requests
import urllib.parse
import wave
import pyaudio
import logging
import re

# .env 파일에서 환경 변수 로드
load_dotenv()

logging.getLogger("langchain").setLevel(logging.ERROR)

# Voicevox 관련 설정
base_url = "http://localhost:50021"

# Google Calendar 관련 키워드
CALENDAR_KEYWORDS = ["일정", "캘린더", "회의", "약속"]


def parse_korean_date(user_input):
    try:
        match = re.search(r"(\d{1,2})월\s*(\d{1,2})일", user_input)
        if match:
            month, day = map(int, match.groups())
            parsed_date = datetime(datetime.now().year, month, day)
            print(f"Debug: Successfully parsed date - {parsed_date}")
            return parsed_date
        else:
            print(f"Debug: Failed to match date format in input - {user_input}")
            return None
    except ValueError as e:
        print(f"Debug: ValueError in parsing date - {e}")
        return None


def analyze_user_intent(user_input):
    if re.search(r"\d{1,2}월\s*\d{1,2}일", user_input):
        return "date_specific"
    if any(keyword in user_input for keyword in CALENDAR_KEYWORDS):
        return "recent"
    return "unknown"


@lru_cache(maxsize=128)
def get_upcoming_events_cached():
    try:
        return get_upcoming_events()
    except Exception as e:
        print(f"Google Calendar API 호출 중 에러 발생: {e}")
        return []


def filter_calendar_by_date(user_input, events):
    intent = analyze_user_intent(user_input)
    print(f"Debug: Detected user intent - {intent}")

    if intent == "recent":
        now = datetime.now(timezone("Asia/Seoul"))
        upcoming_events = sorted(
            events,
            key=lambda event: parser.isoparse(event["time"]).astimezone(
                timezone("Asia/Seoul")
            ),
        )
        for event in upcoming_events:
            event_time = parser.isoparse(event["time"]).astimezone(
                timezone("Asia/Seoul")
            )
            if event_time > now:
                print(f"Debug: Nearest upcoming event - {event}")
                return [event]
        return []

    elif intent == "date_specific":
        try:
            parsed_date = parse_korean_date(user_input)
            if not parsed_date:
                print(f"날짜 파싱 실패: {user_input}")
                return None
            target_date = parsed_date.date()
        except Exception as e:
            print(f"날짜 파싱 중 오류 발생: {e}")
            return None

        print(f"Debug: Target date for filtering - {target_date}")

        filtered_events = []
        for event in events:
            try:
                event_time = parser.isoparse(event["time"]).astimezone(
                    timezone("Asia/Seoul")
                )
                if event_time.date() == target_date:
                    filtered_events.append(event)
            except Exception as e:
                print(f"이벤트 시간 파싱 에러: {e}")
                continue

        print(f"Debug: Filtered events - {filtered_events}")
        return filtered_events

    else:
        print("Debug: Unknown intent detected. No specific action taken.")
        return []


def load_system_prompt(file_path="System_Prompt.txt"):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            prompt_content = file.read()
            print(f"Debug: System prompt loaded successfully from {file_path}")
            return prompt_content
    except Exception as e:
        print(f"Error: Failed to load system prompt from {file_path} - {e}")
        return "Default system prompt: 캐릭터성이 필요합니다. 이 응답은 기본 시스템 프롬프트를 사용합니다."


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

    return speech_filename


def play_with_pyaudio(speech_filename):
    """VB-CABLE로 오디오 파일 재생."""
    p = pyaudio.PyAudio()
    vb_cable_index = 6

    if vb_cable_index is None:
        print("Error: VB-CABLE 장치가 설정되지 않았습니다.")
        return

    wav_file = wave.open(speech_filename, "rb")
    stream = p.open(
        format=p.get_format_from_width(wav_file.getsampwidth()),
        channels=wav_file.getnchannels(),
        rate=wav_file.getframerate(),
        output_device_index=vb_cable_index,  # VB-CABLE 장치 ID 사용
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


def speak_and_play(text):
    speech_filename = speak_with_voicevox(text)

    if speech_filename and os.path.exists(speech_filename):
        play_with_pyaudio(speech_filename)
    else:
        print(f"Error: 음성 파일을 찾을 수 없습니다. 파일 이름: {speech_filename}")


def play_with_multiple_outputs(speech_filename, vb_cable_id, speaker_id):
    """VB-CABLE 및 지정된 스피커로 동시 출력."""
    p = pyaudio.PyAudio()

    # 오디오 파일 열기
    wav_file = wave.open(speech_filename, "rb")
    audio_format = p.get_format_from_width(wav_file.getsampwidth())
    channels = wav_file.getnchannels()
    rate = wav_file.getframerate()

    # VB-CABLE 출력 스트림 생성
    vb_cable_stream = p.open(
        format=audio_format,
        channels=channels,
        rate=rate,
        output_device_index=vb_cable_id,  # VB-CABLE ID
        output=True,
    )

    # 스피커 출력 스트림 생성
    speaker_stream = p.open(
        format=audio_format,
        channels=channels,
        rate=rate,
        output_device_index=speaker_id,  # 스피커 ID
        output=True,
    )

    # 오디오 데이터를 읽어 두 출력 장치로 동시에 전송
    data = wav_file.readframes(1024)
    while data:
        vb_cable_stream.write(data)
        speaker_stream.write(data)
        data = wav_file.readframes(1024)

    # 스트림 정리
    vb_cable_stream.stop_stream()
    vb_cable_stream.close()
    speaker_stream.stop_stream()
    speaker_stream.close()
    wav_file.close()
    p.terminate()


def speak_and_play_multiple(text, vb_cable_id, speaker_id):
    """텍스트를 음성으로 변환 후 VB-CABLE 및 스피커로 출력."""
    speech_filename = speak_with_voicevox(text)

    if speech_filename and os.path.exists(speech_filename):
        play_with_multiple_outputs(speech_filename, vb_cable_id, speaker_id)
    else:
        print(f"Error: 음성 파일을 찾을 수 없습니다. 파일 이름: {speech_filename}")


def generate_response(user_input, session_id):
    llm = ChatOpenAI(
        openai_api_key=os.environ["OPENAI_API_KEY"], model_name="gpt-4", temperature=1
    )

    system_prompt = load_system_prompt()

    if any(keyword in user_input for keyword in CALENDAR_KEYWORDS):
        events = get_upcoming_events_cached()
        filtered_events = filter_calendar_by_date(user_input, events)

        if filtered_events:
            event_descriptions = "\n".join(
                f"시간: {event['time']}, 제목: {event['title']}, 설명: {event['description']}, 위치: {event['location']} "
                for event in filtered_events
            )
            extended_prompt = (
                f"{system_prompt}\n\n"
                f"ナンマンキャット様, 아래는 요청하신 '{user_input}' 관련 일정입니다:\n{event_descriptions}\n"
                "이 정보를 바탕으로 캐릭터성을 유지하며 응답하세요."
            )
        else:
            extended_prompt = (
                f"{system_prompt}\n\n"
                f"ナンマンキャット様, '{user_input}' 관련 일정이 없습니다. 다른 도움을 요청해 주세요."
            )
    else:
        extended_prompt = (
            f"{system_prompt}\n\n"
            f"ナンマンキャット様, '{user_input}'에 대한 직접적인 정보는 없지만, 다른 요청이 있다면 알려주세요."
        )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", extended_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ]
    )

    chain = prompt | llm
    chain_with_memory = RunnableWithMessageHistory(
        chain,
        lambda _: ChatMessageHistory(),
        input_messages_key="question",
        history_messages_key="history",
    )
    response = chain_with_memory.invoke(
        {"question": user_input}, config={"configurable": {"session_id": session_id}}
    )
    return response.content


def chat():
    print("メガミ: 안녕하세요! 무엇을 도와드릴까요?")
    session_id = "unique_session_id"
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["종료", "exit", "quit"]:
            print("メガミ: 안녕히 가세요!")
            break

        response = generate_response(user_input, session_id)
        print(f"メガミ: {response}")

        # 음성 출력 (VB-CABLE ID: 6, 스피커 ID: 4)
        speak_and_play_multiple(response, vb_cable_id=6, speaker_id=4)


if __name__ == "__main__":
    chat()
