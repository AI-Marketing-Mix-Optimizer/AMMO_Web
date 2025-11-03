from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, jsonify, redirect, url_for
import plotly.express as px
import pandas as pd
import os
# report_gen.py 함수
from flask import send_from_directory
from report_gen import generate_llm_report

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

        # 기존 & 변동 각각의 매출/ROI 계산
        def calc_revenue_roi(search_cost, live_cost, event_flag):
            revenue = INTERCEPT + search_cost * SEARCH_COEFF + live_cost * LIVE_COEFF + event_flag * EVENT_COEFF
            total_cost = search_cost + live_cost
            roi = (revenue - total_cost) / (total_cost if total_cost > 0 else 1)
            return revenue, roi

        base_revenue, base_roi = calc_revenue_roi(base_search_cost, base_live_cost, base_event_flag)
        new_revenue, new_roi = calc_revenue_roi(new_search_cost, new_live_cost, new_event_flag)

        #  변화량 계산
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
# PDF 보고서 생성 API
# -----------------------------
@app.route("/generate_report", methods=["POST"])
def generate_report():
    data = request.json or {}

    base_search = float(data.get("base_search_ad_cost",0))
    base_live   = float(data.get("base_live_ad_cost",0))
    new_search  = float(data.get("new_search_ad_cost",0))
    new_live    = float(data.get("new_live_ad_cost",0))
    promo_flag  = 1 if data.get("competitor_event","N") == "Y" else 0

    # 회귀계수 dict
    coeffs = {
        "BETA_0": INTERCEPT,
        "BETA_SEARCH": SEARCH_COEFF,
        "BETA_LIVE": LIVE_COEFF,
        "BETA_EVENT": EVENT_COEFF
    }

    # 리포트 저장 폴더
    output_dir = os.path.join(BASE_DIR, "static", "reports")
    os.makedirs(output_dir, exist_ok=True)

    # 기존 파일 5개 유지 - 초과 시 오래된 순 삭제
    max_files = 5
    pdf_files = sorted(
        [f for f in os.listdir(output_dir) if f.endswith(".pdf")],
        key=lambda x: os.path.getmtime(os.path.join(output_dir, x))
    )

    if len(pdf_files) >= max_files:
        files_to_delete = len(pdf_files) - max_files + 1
        for f in pdf_files[:files_to_delete]:
            try:
                os.remove(os.path.join(output_dir, f))
            except Exception as e:
                print(f"[WARN] 파일 삭제 실패: {f}, {e}")

    #  기존 방식대로 PDF 생성
    pdf_path = generate_llm_report(
        base_search, base_live, promo_flag, coeffs, output_dir,
        new_search, new_live
    )

    return jsonify({
        "success": True,
        "download_url": f"/download_report/{os.path.basename(pdf_path)}"
    })

# -----------------------------
# PDF 파일 다운로드
# -----------------------------
@app.route('/download_report/<path:filename>')
def download_report(filename):
    directory = os.path.join(BASE_DIR, 'static', 'reports')
    return send_from_directory(directory, filename, as_attachment=True)

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
