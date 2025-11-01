from flask import Flask, render_template, request, jsonify, redirect, url_for
import plotly.express as px
import pandas as pd
import os

app = Flask(__name__)

# -----------------------------
# 파일 경로
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEARCH_VOLUME_FILE = os.path.join(BASE_DIR, 'search_volume_total.csv')
LIVE_INFO_FILE = os.path.join(BASE_DIR, 'live_info_B.csv')
ELASTICNET_FILE = os.path.join(BASE_DIR, 'elasticnet_results_experiments_B.csv')

# -----------------------------
# 회귀계수 로드
# -----------------------------
try:
    df = pd.read_csv(ELASTICNET_FILE)
    baseline = df[df['experiment'] == 'baseline']
    SEARCH_COEFF = baseline.loc[baseline['feature'] == 'search_ad_spend_est', 'beta_real'].iloc[0]
    LIVE_COEFF = baseline.loc[baseline['feature'] == 'live_ad_spend_est', 'beta_real'].iloc[0]
    EVENT_COEFF = baseline.loc[baseline['feature'] == 'competitor_event_flag', 'beta_real'].iloc[0]
    INTERCEPT = baseline.loc[baseline['feature'] == 'intercept', 'intercept'].iloc[0]
except Exception as e:
    print(f"[WARN] 회귀계수 로드 실패 → 더미값 사용 ({e})")
    SEARCH_COEFF, LIVE_COEFF, EVENT_COEFF, INTERCEPT = 1321.5, 267.8, 2.2e8, 2.57e8

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
        search_cost = float(data.get("search_ad_cost", 0))
        live_cost = float(data.get("live_ad_cost", 0))
        event_flag = 1.0 if data.get("competitor_event") == "Y" else 0.0

        revenue = INTERCEPT + search_cost * SEARCH_COEFF + live_cost * LIVE_COEFF + event_flag * EVENT_COEFF
        total_cost = search_cost + live_cost
        roi = (revenue - total_cost) / (total_cost if total_cost > 0 else 1)
        base_roi = INTERCEPT / 1.0

        return jsonify({
            "success": True,
            "predicted_revenue": round(max(0, revenue), 0),
            "revenue_change": round(revenue - INTERCEPT, 0),
            "roi": round(roi, 2),
            "roi_change": round(roi - base_roi, 2)
        })
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

# -----------------------------
# 실행
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
