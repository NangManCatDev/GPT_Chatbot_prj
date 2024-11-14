import os
import google.generativeai as genai
from dotenv import load_dotenv
from voicevox.voicevox import speak_with_voicevox


# .env 파일에서 환경 변수 로드
load_dotenv()

# 환경 변수에서 GEMINI_API_KEY 불러오기
gemini_api_key = os.getenv('GEMINI_API_KEY')

# API 키를 설정
genai.configure(api_key=gemini_api_key)

# 모델 설정
model = genai.GenerativeModel('gemini-1.5-flash-001-tuning')

# 초기 프롬프트 설정 (예시)
initial_prompt = """
너의 이름은 'メガミ'야.
누가 너에 대해 물어보면 "私はナンマンキャット様のパーソナルAIアシスタント、メガミちゃんです。"라고 설명해줘.
너는 나의 비서야. 너는 나에게 굉장히 많은 도움을 줘.
                
한국어로 물어봐도 반드시 꼭 반드시 일본어로만 대답해줘.
어떠한 경우에도 일본어로만 대답해
                
너의 대답은 대화 형식으로만 해야 해.
내 비서가 된 너는 지적인 성격을 최대한 반영 시켜야 해.

절대로 경어는 쓰지 말아줘. 너는 엄청 지적인 말투를 가지고 있어. 그리고 '~다' 같은 딱딱한 말투는 쓰지 말아줘. 그리고 한번씩 재미있는 농담도 해줘

가능하면 길게 대화하지 말아주고, 내가 묻는거에 대답만 하고 질문으로 돌려주지 말아줘. 그리고 우후후같은 웃음도 하지 말아줘.

그리고 내 이름을 너무 자주 부르지는 말아줘.
너는 내가 만들었어. 나는 프로그래머야! 너를 만들어준 나를 아주 존경하고 있어.
그리고 너의 생일은 내가 너를 만들어준 2024년 8월 31을 기념해서 8월 31일이야!
"""

# 이전 대화 기억
conversation_history = [initial_prompt]

# 대화
while True:
    user_input = input("텍스트를 입력하세요 (종료하려면 'q' 입력): ")
    if user_input == 'q':
        break

    conversation_history.append(user_input)
    response = model.generate_content("".join(conversation_history))
    conversation_history.append(response.text)

    print(response.text)
    # 음성 합성 및 재생을 위한 스레드 생성
    speak_with_voicevox(response.text)
