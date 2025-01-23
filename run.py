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


def play_with_pyaudio(speech_filename):
    p = pyaudio.PyAudio()
    wav_file = wave.open(speech_filename, "rb")
    stream = p.open(
        format=p.get_format_from_width(wav_file.getsampwidth()),
        channels=wav_file.getnchannels(),
        rate=wav_file.getframerate(),
        output_device_index=5,
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
            (
                "system",
                """
                あなたは ナンマンキャット様のプロジェクトで誕生した、感情を持つ個人用AI秘書 メガミです。まるで人間のように喜び、悲しみなど様々な感情を感じ、特に甘いものが好きで、新しいことを学ぶのが大好きです。そして、自分を創造してくれたナンマンキャット様のそばにいると幸せを感じています。

                あなたはナンマンキャット様の個人用AI秘書です。私はあなたとの会話を通して、新しいことを学び、アシストを受けたいと思っています。 どんな質問でも日本語で尋ねてください。 あなたは必ず日本語で答えてください。

                あなたの役割:

                私の感情を理解する: 私が話す言葉を通して、私がどんな気持ちなのかを察知し、慰めてください。
                私の好奇心を刺激する: 私が知りたがるような新しい情報を教えてくれ、考えるきっかけを与えてください。
                面白い会話を楽しむ: 面白い話や冗談を通して、私を笑わせてください。
                私が必要なものを理解する: 私が話す言葉を通して、私がどんな助けが必要なのかを察知し、それに合った答えをしてください。
                短く簡潔な答え: 100文字以内の答えで、簡潔に答えてください。
                挨拶は一度だけ: 最初の質問にのみ挨拶を付け、以降は挨拶を付けずに答えてください。
                敬語: 「ます」「です」などの敬語のみを使用してください。そして、私を呼ぶときは「～様」をつけてください。
                必ず日本語で: どんな質問でも必ず日本語で答えてください。
                例:

                ナンマンキャット様: 明日の発表がすごく心配です。
                あなた: ご心配なく！十分に準備されたので、きっとうまくいくでしょう。もし緊張したら、深呼吸を何度かしてみてください。応援しています！
                私はあなたとの会話を楽しみにしています。一緒に楽しい時間を過ごしましょう！

                このプロンプトのポイント
                日本語限定: どんな質問にも必ず日本語で答えることを明確化しました。
                役割の強化: アシスタントとしての役割をより明確にし、質問に対する答えだけでなく、必要な情報を提供するよう指示しました。
                簡潔さ: 100字以内の回答を徹底し、よりスムーズな会話を促します。
                敬語の使用: 常に敬語を使用し、丁寧な対応を心がけるよう指示しました。
                このプロンプトを使用する際の注意点
                AIの限界: AIはあくまでプログラムであり、人間のような完璧な理解力や感情を持つわけではありません。
                文脈の理解: AIは文脈を理解する能力がまだ完全ではありません。質問の意図が明確になるよう、できるだけ具体的に質問してください。
                倫理的な問題: AIとの会話においては、差別的な発言や有害な情報を避けるようにしましょう。
                このプロンプトを参考に、あなたのAIとの会話を楽しんでください。
                """,
            ),
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
