# ============================================
# router.py
# ============================================
import os
from openai import OpenAI
from dotenv import load_dotenv
from util import llm_call, extract_xml
from natural_language_parser import parse_user_input

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Intent Routes 정의
intent_routes = {
    "parse_budget": """
        너는 사용자의 입력이 '예산, 배분, 프로모션, 검색광고, 라이브, 얼마, 원, 억, 증가/감소' 등
        숫자/광고비/프로모션 설정 관련이면 parse_budget으로 분류한다.
        JSON 출력하는 파서가 작동해야 하는 경우가 이 경우다.
    """,
    "analysis_question": """
        광고 분석, ROI 변화 해석, 그래프 해석, 광고 효율 문의, 매출 관련 질의, 효과적인 광고 채널, 성과 분석 등은 analysis_question으로 분류한다.
    """,
    "general_chat": """
        일반 대화, 감정 표현, 챗봇과의 자연스러운 대화는 general_chat으로 분류한다.
    """,
    "unknown": """
        위에 해당하지 않으면 unknown으로 분류한다.
    """
}


# Intent 분류 함수
def classify_intent(user_input: str) -> str:
    options = list(intent_routes.keys())

    prompt = f"""
    아래 사용자 입력이 어떤 카테고리인지 판단하시오.
    카테고리: {options}

    반드시 XML로만 출력:

    <reasoning>
    판단 근거를 간단히 설명
    </reasoning>

    <selection>
    카테고리 이름 (parse_budget / analysis_question / general_chat / unknown 중 하나)
    </selection>

    사용자 입력:
    {user_input}
    """

    llm_output = llm_call(prompt)
    selected = extract_xml(llm_output, "selection").strip().lower()

    if selected not in options:
        selected = "unknown"

    return selected


# 3) Smart Router (메인 실행)
def smart_router(user_input: str, intent: str):
    # 예산/프로모션 파싱 → natural_language_parser 호출
    if intent == "parse_budget":
        return parse_user_input(user_input)

    # 분석 질문 → 분석 모델 호출
    elif intent == "analysis_question":
        analysis_prompt = f"""
        너는 광고 예산 및 퍼포먼스 분석 전문 어시스턴트이다.

        # 출력 형식 규칙 (중요)
        1) 절대 한 문단으로 뭉치지 말 것.
        2) 각 번호는 반드시 **줄바꿈 1회 후 시작**할 것.
        3) 번호 안의 하위 bullet은 앞에 '-'를 붙이고 줄바꿈을 넣을 것.
        4) 문장 끝마다 자연스러운 개행을 유지할 것.
        5) HTML이나 Markdown 없이 순수 텍스트 줄바꿈만 사용한다.
        6) 강조를 위한 마크다운 문법 사용 금지.

        질문:
        {user_input}

        출력:
        분석 기반 답변.
        """
        return llm_call(analysis_prompt)

    # 일반 대화
    elif intent == "general_chat":
        chat_prompt = f"""
        너는 친절한 일반 대화 챗봇이다.

        사용자 메시지:
        {user_input}

        자연스럽고 인간적인 톤으로 답해주세요.
        """
        return llm_call(chat_prompt)

    # 알 수 없는 경우
    else:
        return "요청을 이해하지 못했습니다. 예산/분석 관련 질문으로 다시 입력해주세요."
