# ============================================
# result_analysis.py
# ============================================
import os
from dotenv import load_dotenv
from openai import OpenAI

# OpenAI API 초기화
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def interpret_simulation_result(
        base_search, base_live, new_search, new_live,
        base_revenue, new_revenue, base_roi, new_roi,
        coeffs
):
    #LLM을 통해 ROI 시뮬레이션 결과를 자연어로 해석해주는 함수
    prompt = f"""
    # 역할
    너는 마케팅 데이터 분석 보고서를 설명하는 AI 어시스턴트야.
    아래 입력값과 계산 결과를 보고 사용자가 이해하기 쉽게 한글로 자연어 설명을 생성해줘.
    전문용어 대신 직관적으로, 간결하게 설명해.

    # 회귀계수
    - 검색광고 계수 (BETA_SEARCH): {coeffs['BETA_SEARCH']:.2f}
    - 라이브커머스 계수 (BETA_LIVE): {coeffs['BETA_LIVE']:.2f}
    - 경쟁사 이벤트 계수 (BETA_EVENT): {coeffs['BETA_EVENT']:.2f}
    - 절편 (INTERCEPT): {coeffs['BETA_0']:.2f}

    # 사용자의 입력
    - 기존 검색광고 예산: {base_search:,.0f} 원
    - 기존 라이브 예산: {base_live:,.0f} 원
    - 변경 후 검색광고 예산: {new_search:,.0f} 원
    - 변경 후 라이브 예산: {new_live:,.0f} 원

    # 계산 결과
    - 기존 매출: {base_revenue:,.0f} 원
    - 변경 후 매출: {new_revenue:,.0f} 원
    - 기존 ROI: {base_roi:.2f}
    - 변경 후 ROI: {new_roi:.2f}
    - ROI 변화: {(new_roi - base_roi):+.2f}

    # 요청사항
    1. 매출과 ROI가 증가했는지 감소했는지 서술.
    2. 어떤 광고 채널이 매출 변화에 더 큰 영향을 준 것으로 보이는지 추론.
    3. 수치를 기반으로 간단한 인사이트 한 문단으로 정리해줘.
    4. 마지막에 전문가들이 봤을 때 도움되도록 전문용어를 사용한 설명을 새로운 단락으로 추가해서 생성해줘.
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are an expert marketing analyst who explains numerical results clearly."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.5,
    )

    interpretation = response.choices[0].message.content.strip()
    return interpretation
