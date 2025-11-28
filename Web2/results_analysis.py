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
        너는 실전 마케팅 데이터 분석을 수행하는 AI 컨설턴트다.
        사용자가 시뮬레이션 결과를 ‘빠르게 이해할 수 있도록’ 구조화된 분석을 제공해라.

        # 출력 형식 (반드시 이 구조를 유지)
        [1] 한 줄 요약  
        - 매출/ROI가 어떻게 변했는지 한 문장으로 요약

        [2] 매출 변화 해석  
        - 증가/감소 이유를 직관적으로 설명  
        - 어떤 채널이 기여했는지 수치를 근거로 서술

        [3] ROI 변화 해석  
        - ROI 증감 원인  
        - 비용 대비 효율 변화 설명

        [4] 원인 분석 (광고 채널별 영향력)  
        - 검색광고 계수 vs 라이브커머스 계수 비교  
        - 어떤 채널이 총 매출 변화에 더 크게 작용했는지 분석

        [5] 실행 가능한 인사이트  
        - 예산 조정 방향  
        - 앞으로의 시나리오 제안 (예: 검색광고 중심 / 라이브커머스 최적화 등)

        [6] 전문가용 해석 (새 단락)  
        - 회귀계수 기반의 정량 분석  
        - 통계·마케팅 용어 사용  
        - ‘전문가 리뷰용’으로 더 깊이 있는 해석 제공

        # 회귀계수
        검색광고 계수(BETA_SEARCH): {coeffs['BETA_SEARCH']:.2f}
        라이브커머스 계수(BETA_LIVE): {coeffs['BETA_LIVE']:.2f}
        경쟁사 이벤트 계수(BETA_EVENT): {coeffs['BETA_EVENT']:.2f}
        절편(INTERCEPT): {coeffs['BETA_0']:.2f}

        # 사용자의 입력
        기존 검색광고 예산: {base_search:,.0f} 원
        기존 라이브 예산: {base_live:,.0f} 원
        변경 후 검색광고 예산: {new_search:,.0f} 원
        변경 후 라이브 예산: {new_live:,.0f} 원

        # 계산 결과
        기존 매출: {base_revenue:,.0f} 원
        변경 후 매출: {new_revenue:,.0f} 원
        기존 ROI: {base_roi:.2f}
        변경 후 ROI: {new_roi:.2f}
        ROI 변화: {(new_roi - base_roi):+.2f}

        # 추가 요구사항
        - 문장은 부드럽고 자연스럽게
        - 과장하지 말고 사용자의 입력과 계산결과의 실제 수치를 근거로 설명
        - 전문가용 섹션은 별도로 구분되게 작성
        # 절대 수정 금지 규칙
        - 모든 숫자는 절대 재계산하거나 변환하지 말고, 입력된 그대로 출력할 것
        - '원' 단위, 천 단위 콤마 등을 AI가 임의로 변경하거나 보정하지 말 것
        - 실제 숫자 뒤에 추가로 0을 붙이거나 빼지 말 것
        - 소수점 잘 구별해서 금액 계산할것
        - 입력된 숫자의 자리수를 그대로 유지할 것
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
