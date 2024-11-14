from dotenv import load_dotenv
import google.generativeai as genai
import os
 
 
# .env 파일에서 환경 변수 로드
load_dotenv()

# 환경 변수에서 GEMINI_API_KEY 불러오기
gemini_api_key = os.getenv('GEMINI_API_KEY')

# 제미나이 모델들 확인
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)