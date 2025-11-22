# ============================================
# natural_language_parser.py
# ============================================
import os
from openai import OpenAI
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def parse_user_input(user_input: str):
    # 자연어 입력값 파싱
    prompt = f"""
    # 역할
    너는 사용자의 자연어 입력에서 특정 값을 파싱하는 모델이야.
    아래 입력문에서 원하는 데이터를 JSON 형식으로 추출해줘.
    기존 프로모션에 대한 얘기가 없다면 프로모션 진행하지 않음.
    변동 프로모션에 대한 얘기가 없다면 프로모션 진행하지 않음.
    기존 예산에 대한 얘기가 없다면 검색광고 100000000원 라이브 50000000원

    # 입력 예시 1
    "총 예산은 1,000,000,000원으로 하고 경쟁사는 프로모션하는 걸로 해줘"

    # 출력 예시
    {{
        "총 예산": 1000000000,
        "기존 검색광고 예산": 100000000,
        "기존 라이브광고 예산": 50000000,
        "기존 프로모션 여부": 0,
        "변동 검색광고 예산": 총 예산의 50%를 float 형식으로,
        "변동 라이브광고 예산": 총 예산의 50%를 float 형식으로,
        "변동 프로모션 여부": 1
    }}

    # 입력 예시 2
    "검색광고 예산은 700,000,000원으로 하고 라이브는 400000000원이야"

    # 출력 예시
    {{
        "총 예산": 1100000000,
        "기존 검색광고 예산": 100000000,
        "기존 라이브광고 예산": 50000000,
        "기존 프로모션 여부": 0,
        "변동 검색광고 예산": 700000000,
        "변동 라이브광고 예산": 400000000,
        "변동 프로모션 여부": 0
    }}
    
    # 입력 예시 3
    "기존 검색광고 5억 라이브 3억 진행, 변동 예산은 검색광고 칠억 라이브 사억"

    # 출력 예시
    {{
        "총 예산": 1100000000,
        "기존 검색광고 예산": 500000000,
        "기존 라이브광고 예산": 300000000,
        "기존 프로모션 여부": 1,
        "변동 검색광고 예산": 700000000,
        "변동 라이브광고 예산": 400000000,
        "변동 프로모션 여부": 0
    }}
    
    # 실제 입력문
    {user_input}

    # 출력 (JSON 형식만)
    반드시 JSON만 출력하고 코드블록(```json`)을 사용하지 말 것.
    
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a precise natural language parser that outputs valid JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1,
    )

    parsed_output = response.choices[0].message.content.strip()
    return parsed_output


if __name__ == "__main__":
    user_input = input("자연어 입력: ")
    result = parse_user_input(user_input)
    print("\n[파싱 결과]\n", result)
