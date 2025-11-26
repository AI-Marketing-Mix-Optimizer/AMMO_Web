from flask import Flask, render_template, request, jsonify
import plotly.express as px
import pandas as pd
import os
import requests

# -----------------------------
# 기본 경로 설정
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, "templates"),
            static_folder=os.path.join(BASE_DIR, "static"))


# -----------------------------
# 파일 경로
# -----------------------------
SEARCH_VOLUME_FILE = os.path.join(BASE_DIR, 'search_volume_total.csv')
LIVE_INFO_FILE = os.path.join(BASE_DIR, 'live_info_B.csv')
ELASTICNET_FILE = os.path.join(BASE_DIR, 'elasticnet_results_experiments_B.csv')


# -----------------------------
# 회귀계수 (고정값)
# -----------------------------
SEARCH_COEFF = 1399.99176152645
LIVE_COEFF = 399.270203778113
EVENT_COEFF = 1243765335.801
INTERCEPT = 1471759280.85189

# -----------------------------
# 쇼핑라이브 시각화
# -----------------------------
try:
    live_df = pd.read_csv(LIVE_INFO_FILE)
    live_df['date'] = pd.to_datetime(live_df['date'])
    days = ['월', '화', '수', '목', '금', '토', '일']
    live_df['요일'] = live_df['date'].dt.weekday.map(dict(zip(range(7), days)))

    df_day = live_df.groupby('요일', sort=False)['viewer_count'].mean().reindex(days).reset_index()
    fig_day = px.bar(df_day, x='요일', y='viewer_count', title='', color_discrete_sequence=['#00b4d8'])
    day_chart = fig_day.to_html(full_html=False)

    df_promo = live_df.copy()
    df_promo['프로모션'] = df_promo['promotion_flag'].map({1: '진행', 0: '없음'})
    fig_promo = px.box(df_promo, x='프로모션', y='viewer_count',
                       title='', color_discrete_sequence=['#0077b6'])
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

        base_search_cost = float(data.get("base_search_ad_cost", 0))
        base_live_cost = float(data.get("base_live_ad_cost", 0))
        base_event_flag = 1.0 if data.get("base_competitor_event") == "Y" else 0.0

        new_search_cost = float(data.get("new_search_ad_cost", 0))
        new_live_cost = float(data.get("new_live_ad_cost", 0))
        new_event_flag = 1.0 if data.get("new_competitor_event") == "Y" else 0.0

        def calc_revenue_roi(search_cost, live_cost, event_flag):
            revenue = INTERCEPT + search_cost * SEARCH_COEFF + live_cost * LIVE_COEFF + event_flag * EVENT_COEFF
            total_cost = search_cost + live_cost
            roi = (revenue - total_cost) / (total_cost if total_cost > 0 else 1)
            return revenue, roi

        base_revenue, base_roi = calc_revenue_roi(base_search_cost, base_live_cost, base_event_flag)
        new_revenue, new_roi = calc_revenue_roi(new_search_cost, new_live_cost, new_event_flag)

        revenue_change = new_revenue - base_revenue
        roi_change = new_roi - base_roi

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
# 임시 챗봇 기능 (파싱 모의)
# -----------------------------
@app.route("/chatbot", methods=["POST"])
def chatbot():
    data = request.get_json()
    text = data.get("text", "")

    # --- 1. 임시 파싱 규칙 ---
    if "검색" in text and "늘려" in text:
        new_search = 20000000
    elif "검색" in text and "줄여" in text:
        new_search = 5000000
    else:
        new_search = 10000000

    if "라이브" in text and "줄여" in text:
        new_live = 3000000
    elif "라이브" in text and "늘려" in text:
        new_live = 8000000
    else:
        new_live = 5000000

    event = "Y" if "이벤트" in text else "N"

    parsed = {
        "new_search_ad_cost": new_search,
        "new_live_ad_cost": new_live,
        "new_competitor_event": event,
        "summary": f"검색광고비 {new_search:,}원, 라이브광고비 {new_live:,}원, 이벤트 {event}"
    }

    # --- 2. 시뮬레이션 실행 ---
    try:
        sim_res = requests.post("http://localhost:5000/simulate", json={
            "base_search_ad_cost": 10000000,
            "base_live_ad_cost": 5000000,
            "base_competitor_event": "N",
            "new_search_ad_cost": parsed["new_search_ad_cost"],
            "new_live_ad_cost": parsed["new_live_ad_cost"],
            "new_competitor_event": parsed["new_competitor_event"]
        }).json()
    except Exception as e:
        return jsonify({"success": False, "message": f"시뮬레이션 오류: {e}"}), 500

    # --- 3. 챗봇 응답 ---
    return jsonify({
        "success": True,
        "summary": parsed["summary"],
        "result": sim_res
    })


# -----------------------------
# 페이지 라우팅
# -----------------------------
@app.route("/")
def home():
    print("[DEBUG] 렌더링 템플릿: home.html")
    return render_template("home.html")

@app.route("/dashboard")
def dashboard():
    print("[DEBUG] 렌더링 템플릿: dashboard.html")
    return render_template("dashboard.html",
                           day_chart=day_chart,
                           promo_chart=promo_chart)

# -----------------------------
# 실행
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
