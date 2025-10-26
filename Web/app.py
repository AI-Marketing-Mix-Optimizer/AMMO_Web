from flask import Flask, render_template, request, jsonify
import plotly.express as px
import pandas as pd
import numpy as np
import os

app = Flask(__name__)

# -----------------------------
# 📂 절대경로 기반 파일 설정
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEARCH_VOLUME_FILE = os.path.join(BASE_DIR, 'search_volume_total.csv')
LIVE_INFO_FILE = os.path.join(BASE_DIR, 'live_info_B.csv')
PROXY_SALES_FILE = os.path.join(BASE_DIR, 'proxy_sales_B.csv')
ELASTICNET_FILE = os.path.join(BASE_DIR, 'elasticnet_results_experiments_B.csv')

# -----------------------------
# 1. 회귀계수 로딩 (시뮬레이션용)
# -----------------------------
try:
    proxy_sales_df = pd.read_csv(PROXY_SALES_FILE)
    elasticnet_df = pd.read_csv(ELASTICNET_FILE)
    baseline_coeffs = elasticnet_df[elasticnet_df['experiment'] == 'baseline']

    SEARCH_COEFF = baseline_coeffs[baseline_coeffs['feature'] == 'search_ad_spend_est']['beta_real'].iloc[0]
    LIVE_COEFF = baseline_coeffs[baseline_coeffs['feature'] == 'live_ad_spend_est']['beta_real'].iloc[0]
    EVENT_COEFF = baseline_coeffs[baseline_coeffs['feature'] == 'competitor_event_flag']['beta_real'].iloc[0]
    INTERCEPT = baseline_coeffs[baseline_coeffs['feature'] == 'intercept']['intercept'].iloc[0]

except Exception as e:
    print(f"[WARN] 회귀계수 로딩 실패 → 더미값 사용 ({e})")
    SEARCH_COEFF = 1321.5
    LIVE_COEFF = 267.8
    EVENT_COEFF = 220017488.0
    INTERCEPT = 257554070.0


# -----------------------------
# 2. 쇼핑라이브 시각화 데이터 생성
# -----------------------------
try:
    live_info_df = pd.read_csv(LIVE_INFO_FILE)
    live_info_df['date'] = pd.to_datetime(live_info_df['date'])
    day_order = ['월', '화', '수', '목', '금', '토', '일']
    day_map = dict(zip(range(7), day_order))
    live_info_df['요일'] = live_info_df['date'].dt.weekday.map(day_map)
    live_info_df['카테고리'] = 'B'

    df_day = live_info_df.groupby('요일', sort=False)['viewer_count'].mean().reset_index()
    df_day['카테고리'] = 'B'
    df_day['요일'] = pd.Categorical(df_day['요일'], categories=day_order, ordered=True)
    df_day = df_day.sort_values('요일')

    fig_day = px.bar(df_day, x='요일', y='viewer_count', color='카테고리',
                     color_discrete_map={'B': '#9BE8D8'},
                     title='[카테고리 B] 요일별 평균 시청자 수')
    day_chart = fig_day.to_html(full_html=False)

    df_promo = live_info_df[['viewer_count', 'promotion_flag']].copy()
    df_promo['프로모션'] = df_promo['promotion_flag'].apply(lambda x: '진행' if x == 1 else '없음')
    df_promo['카테고리'] = 'B'

    fig_promo = px.box(df_promo, x='프로모션', y='viewer_count', color='카테고리',
                       color_discrete_map={'B': '#9BE8D8'},
                       title='[카테고리 B] 프로모션 여부별 시청자 수 비교')
    promo_chart = fig_promo.to_html(full_html=False)

except Exception as e:
    print(f"[WARN] 쇼핑라이브 차트 생성 실패 ({e})")
    day_chart = "<div>Live Day Chart Error</div>"
    promo_chart = "<div>Live Promo Chart Error</div>"


# -----------------------------
# 3. 검색광고 데이터 API
# -----------------------------
@app.route('/data/search_volume')
def get_search_volume():
    try:
        df = pd.read_csv(SEARCH_VOLUME_FILE)
        return df.to_csv(index=False)
    except Exception as e:
        return f"Error loading CSV: {e}", 500


# -----------------------------
# 4. ROI 시뮬레이션 API
# -----------------------------
@app.route('/simulate', methods=['POST'])
def simulate():
    try:
        data = request.json
        search_ad_cost = float(data.get('search_ad_cost', 0))
        live_ad_cost = float(data.get('live_ad_cost', 0))
        competitor_event_flag = 1.0 if data.get('competitor_event', 'N') == 'Y' else 0.0

        predicted_revenue = (
            INTERCEPT +
            (search_ad_cost * SEARCH_COEFF) +
            (live_ad_cost * LIVE_COEFF) +
            (competitor_event_flag * EVENT_COEFF)
        )

        total_cost = search_ad_cost + live_ad_cost
        roi_denominator = total_cost if total_cost > 0 else 1.0
        roi = (predicted_revenue - total_cost) / roi_denominator

        BASE_ROI = (INTERCEPT - 0) / 1.0
        revenue_change = predicted_revenue - INTERCEPT
        roi_change = roi - BASE_ROI

        predicted_revenue = max(0, predicted_revenue)

        return jsonify({
            'success': True,
            'predicted_revenue': round(predicted_revenue, 0),
            'revenue_change': round(revenue_change, 0),
            'roi': round(roi, 2),
            'roi_change': round(roi_change, 2)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


# -----------------------------
# 5. 메인 페이지
# -----------------------------
@app.route('/')
def index():
    return render_template('index.html',
                           day_chart=day_chart,
                           promo_chart=promo_chart)


# -----------------------------
# 6. 실행
# -----------------------------
if __name__ == '__main__':
    app.run(debug=True)
