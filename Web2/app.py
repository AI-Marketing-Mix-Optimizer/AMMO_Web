from flask import Flask, render_template, request, jsonify, redirect, url_for
import plotly.express as px
import pandas as pd
import os
import re
import json

from results_analysis import interpret_simulation_result
from natural_language_parser import parse_user_input

app = Flask(__name__)

# -----------------------------
# 파일 경로
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEARCH_VOLUME_FILE = os.path.join(BASE_DIR, 'search_volume_total.csv')
LIVE_INFO_FILE = os.path.join(BASE_DIR, 'live_info_B.csv')
ELASTICNET_FILE = os.path.join(BASE_DIR, 'elasticnet_results_experiments_B.csv')
#
# # -----------------------------
# # 회귀계수 로드
# # -----------------------------
# try:
#     df = pd.read_csv(ELASTICNET_FILE)
#     baseline = df[df['experiment'] == 'baseline']
#     SEARCH_COEFF = baseline.loc[baseline['feature'] == 'search_ad_spend_est', 'beta_real'].iloc[0]
#     LIVE_COEFF = baseline.loc[baseline['feature'] == 'live_ad_spend_est', 'beta_real'].iloc[0]
#     EVENT_COEFF = baseline.loc[baseline['feature'] == 'competitor_event_flag', 'beta_real'].iloc[0]
#     INTERCEPT = baseline.loc[baseline['feature'] == 'intercept', 'intercept'].iloc[0]
# except Exception as e:
#     print(f"[WARN] 회귀계수 로드 실패 → 더미값 사용 ({e})")
#     SEARCH_COEFF, LIVE_COEFF, EVENT_COEFF, INTERCEPT = 1321.5, 267.8, 2.2e8, 2.57e8

SEARCH_COEFF = 1399.99176152645
LIVE_COEFF = 399.270203778113
EVENT_COEFF = 1243765335.801
INTERCEPT = 1471759280.85189

# -----------------------------
# 쇼핑라이브 시각화 데이터
# -----------------------------
try:
    live_df = pd.read_csv(LIVE_INFO_FILE)
    live_df['date'] = pd.to_datetime(live_df['date'])
    days = ['월', '화', '수', '목', '금', '토', '일']
    live_df['요일'] = live_df['date'].dt.weekday.map(dict(zip(range(7), days)))

    df_day = live_df.groupby('요일', sort=False)['viewer_count'].mean().reindex(days).reset_index()
    fig_day = px.bar(df_day, x='요일', y='viewer_count', title='',
                     color_discrete_sequence=['#00b4d8'])
    day_chart = fig_day.to_html(full_html=False)

    df_promo = live_df.copy()
    df_promo['프로모션'] = df_promo['promotion_flag'].map({1: '진행', 0: '없음'})
    fig_promo = px.box(df_promo, x='프로모션', y='viewer_count',
                       title='',
                       color_discrete_sequence=['#0077b6'])
    promo_chart = fig_promo.to_html(full_html=False)

except Exception as e:
    print(f"[WARN] 시각화 데이터 로딩 실패 ({e})")
    day_chart = "<div>Chart Error</div>"
    promo_chart = "<div>Chart Error</div>"

# -----------------------------
# 검색광고 데이터 API
# -----------------------------
@app.route("/data/search_volume")
def get_search_volume():
    try:
        df = pd.read_csv(SEARCH_VOLUME_FILE)
        return df.to_csv(index=False)
    except Exception as e:
        return f"Error loading CSV: {e}", 500

# -----------------------------
# ROI 시뮬레이션 API
# -----------------------------
@app.route("/simulate", methods=["POST"])
def simulate():
    try:
        data = request.get_json()

        # 기존 (base) 입력값
        base_search_cost = float(data.get("base_search_ad_cost", 0))
        base_live_cost = float(data.get("base_live_ad_cost", 0))
        base_event_flag = 1.0 if data.get("base_competitor_event") == "Y" else 0.0

        # 변동 (new) 입력값
        new_search_cost = float(data.get("new_search_ad_cost", 0))
        new_live_cost = float(data.get("new_live_ad_cost", 0))
        new_event_flag = 1.0 if data.get("new_competitor_event") == "Y" else 0.0

        # 매출 & ROI 계산
        def calc_revenue_roi(search_cost, live_cost, event_flag):
            revenue = INTERCEPT + search_cost * SEARCH_COEFF + live_cost * LIVE_COEFF + event_flag * EVENT_COEFF
            total_cost = search_cost + live_cost
            roi = (revenue - total_cost) / (total_cost if total_cost > 0 else 1)
            return revenue, roi

        base_revenue, base_roi = calc_revenue_roi(base_search_cost, base_live_cost, base_event_flag)
        new_revenue, new_roi = calc_revenue_roi(new_search_cost, new_live_cost, new_event_flag)
        revenue_change = new_revenue - base_revenue
        roi_change = new_roi - base_roi

        #  LLM 해석 제거 — 계산만 반환
        return jsonify({
            "success": True,
            "base_revenue": round(base_revenue, 0),
            "new_revenue": round(new_revenue, 0),
            "revenue_change": round(revenue_change, 0),
            "base_roi": round(base_roi, 2),
            "new_roi": round(new_roi, 2),
            "roi_change": round(roi_change, 2)
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


# -----------------------------
# chatbot API
# -----------------------------
def extract_json(text: str):
    # ```json 등 제거
    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text)

    # JSON { } 블록만 추출
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        return match.group(0).strip()
    return text

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_msg = data.get("message", "")

    # 1) 자연어 → JSON 파싱
    parsed_json = parse_user_input(user_msg)
    clean_json = extract_json(parsed_json)

    try:
        parsed = json.loads(clean_json)
    except:
        return jsonify({"reply": "자연어 파싱 JSON 오류\n" + parsed_json})

    # 2) JSON 값 추출
    base_search = float(parsed.get("기존 검색광고 예산", 0))
    base_live = float(parsed.get("기존 라이브광고 예산", 0))
    base_event_flag = int(parsed.get("기존 프로모션 여부", 0))
    new_search = float(parsed.get("변동 검색광고 예산", 0))
    new_live = float(parsed.get("변동 라이브광고 예산", 0))
    new_event_flag = int(parsed.get("변동 프로모션 여부", 0))

    # 3) 계산 로직
    def calc_revenue_roi(search_cost, live_cost, event_flag):
        revenue = (
            INTERCEPT
            + search_cost * SEARCH_COEFF
            + live_cost * LIVE_COEFF
            + event_flag * EVENT_COEFF
        )
        total_cost = search_cost + live_cost
        roi = (revenue - total_cost) / (total_cost if total_cost > 0 else 1)
        return revenue, roi

    # 기존 시나리오
    base_revenue, base_roi = calc_revenue_roi(base_search, base_live, base_event_flag)

    # 변경 시나리오
    new_revenue, new_roi = calc_revenue_roi(new_search, new_live, new_event_flag)

    # 변화 계산
    revenue_change = new_revenue - base_revenue
    roi_change = new_roi - base_roi

    # 4) 시뮬레이션 URL 전송 (기존/변동 모두)
    sim_url = url_for(
        'chat_simulate',
        base_search=base_search,
        base_live=base_live,
        base_event=base_event_flag,
        new_search=new_search,
        new_live=new_live,
        new_event=new_event_flag
    )
    TAP = "&nbsp;" * 5
    # 5) reply 응답
    reply = f"""
        예산 시뮬레이션 결과<br><br>

        ■ 총 예산: {parsed.get('총 예산', 0):,}원<br>
        
        ■ 기존 예산<br> 
        {TAP}검색광고: {base_search:,.0f}원<br> {TAP}라이브광고: {base_live:,.0f}원<br>
        ■ 기존 프로모션: {'YES' if base_event_flag else 'NO'}<br>
        
        ■ 변동 예산<br>
        {TAP}검색광고: {new_search:,.0f}원<br> {TAP}라이브광고: {new_live:,.0f}원<br>
        ■ 변동 프로모션: {'YES' if new_event_flag else 'NO'}<br><br>
        
        ■ 매출 변화: {revenue_change:,.0f}원<br>
        ■ ROI 변화: {roi_change:.2f}<br><br>

        <a href="{sim_url}" target="_blank">시뮬레이션 화면으로 이동</a>
    """

    return jsonify({"reply": reply})



# -----------------------------
# LLM 해석
# -----------------------------
@app.route("/interpret", methods=["POST"])
def interpret():
    try:
        data = request.get_json()
        coeffs = {
            "BETA_0": INTERCEPT,
            "BETA_SEARCH": SEARCH_COEFF,
            "BETA_LIVE": LIVE_COEFF,
            "BETA_EVENT": EVENT_COEFF
        }
        text = interpret_simulation_result(
            data["base_search_ad_cost"],
            data["base_live_ad_cost"],
            data["new_search_ad_cost"],
            data["new_live_ad_cost"],
            data["base_revenue"],
            data["new_revenue"],
            data["base_roi"],
            data["new_roi"],
            coeffs
        )
        return jsonify({"success": True, "analysis": text})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


# -----------------------------
# 페이지 라우팅
# -----------------------------
@app.route("/")
def home():
    """앱 실행 시 홈 화면이 기본"""
    return render_template("home.html")

@app.route("/dashboard")
def dashboard():
    """분석·시뮬레이션·소개 통합"""
    return render_template("dashboard.html",
                           day_chart=day_chart,
                           promo_chart=promo_chart)

# URL 누르면 실행 chat-simulate 새창 생성
@app.route("/chat-simulate")
def chat_simulate():
    # URL 파라미터 읽기
    base_search = request.args.get("base_search", type=float, default=0)
    base_live = request.args.get("base_live", type=float, default=0)
    new_search = request.args.get("new_search", type=float, default=0)
    new_live = request.args.get("new_live", type=float, default=0)
    base_event = request.args.get("base_event", type=int, default=0)
    new_event = request.args.get("new_event", type=int, default=0)

    # 기존 시뮬레이션 계산 로직 재사용
    def calc_revenue_roi(search_cost, live_cost, event_flag):
        revenue = INTERCEPT \
                  + search_cost * SEARCH_COEFF \
                  + live_cost * LIVE_COEFF \
                  + event_flag * EVENT_COEFF

        total_cost = search_cost + live_cost
        roi = (revenue - total_cost) / (total_cost if total_cost > 0 else 1)
        return revenue, roi

    # 기존 시나리오 & 변경 시나리오
    base_revenue, base_roi = calc_revenue_roi(base_search, base_live, base_event)
    new_revenue, new_roi = calc_revenue_roi(new_search, new_live, new_event)

    # 변화값 계산
    revenue_change = new_revenue - base_revenue
    roi_change = new_roi - base_roi

    # 템플릿 렌더링
    return render_template(
        "chat_simulate.html",
        # 계산 값 전달 (챗봇 간단 문자용)
        base_revenue=round(base_revenue, 0),
        new_revenue=round(new_revenue, 0),
        revenue_change=round(revenue_change, 0),
        base_roi=round(base_roi, 2),
        new_roi=round(new_roi, 2),
        roi_change=round(roi_change, 2),
        # 파싱 값 전달
        base_search=base_search,
        base_live=base_live,
        new_search=new_search,
        new_live=new_live,
        promo_flag_base=base_event,
        promo_flag_new=new_event,
        # 계수 전달
        INTERCEPT=INTERCEPT,
        SEARCH_COEFF=SEARCH_COEFF,
        LIVE_COEFF=LIVE_COEFF,
        EVENT_COEFF=EVENT_COEFF
    )


# -----------------------------
# 실행
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
