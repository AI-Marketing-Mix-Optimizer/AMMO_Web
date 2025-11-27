from flask import Flask, render_template, request, jsonify, redirect, url_for
import plotly.express as px
import pandas as pd
import os
import re
import json
from dotenv import load_dotenv

load_dotenv()

from util import llm_call
from results_analysis import interpret_simulation_result
from natural_language_parser import parse_user_input
from router import smart_router

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEARCH_VOLUME_FILE = os.path.join(BASE_DIR, 'search_volume_total.csv')
LIVE_INFO_FILE = os.path.join(BASE_DIR, 'live_info_B.csv')
ELASTICNET_FILE = os.path.join(BASE_DIR, 'elasticnet_results_experiments_B.csv')

SEARCH_COEFF = 1399.99176152645
LIVE_COEFF = 399.270203778113
EVENT_COEFF = 1243765335.801
INTERCEPT = 1471759280.85189

try:
    live_df = pd.read_csv(LIVE_INFO_FILE)
    live_df['date'] = pd.to_datetime(live_df['date'])
    days = ['월', '화', '수', '목', '금', '토', '일']
    live_df['요일'] = live_df['date'].dt.weekday.map(dict(zip(range(7), days)))

    df_day = live_df.groupby('요일', sort=False)['viewer_count'].mean().reindex(days).reset_index()
    fig_day = px.bar(df_day, x='요일', y='viewer_count', color_discrete_sequence=['#00b4d8'])
    day_chart = fig_day.to_html(full_html=False)

    df_promo = live_df.copy()
    df_promo['프로모션'] = df_promo['promotion_flag'].map({1: '진행', 0: '없음'})
    fig_promo = px.box(df_promo, x='프로모션', y='viewer_count', color_discrete_sequence=['#0077b6'])
    promo_chart = fig_promo.to_html(full_html=False)

except Exception:
    day_chart = "<div>Chart Error</div>"
    promo_chart = "<div>Chart Error</div>"


@app.route("/data/search_volume")
def get_search_volume():
    try:
        df = pd.read_csv(SEARCH_VOLUME_FILE)
        return df.to_csv(index=False)
    except Exception as e:
        return f"Error loading CSV: {e}", 500


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

        def calc(search_cost, live_cost, event_flag):
            revenue = (
                INTERCEPT
                + search_cost * SEARCH_COEFF
                + live_cost * LIVE_COEFF
                + event_flag * EVENT_COEFF
            )
            total = search_cost + live_cost
            roi = (revenue - total) / (total if total > 0 else 1)
            return revenue, roi

        base_rev, base_roi = calc(base_search_cost, base_live_cost, base_event_flag)
        new_rev, new_roi = calc(new_search_cost, new_live_cost, new_event_flag)

        return jsonify({
            "success": True,
            "base_revenue": round(base_rev, 0),
            "new_revenue": round(new_rev, 0),
            "revenue_change": round(new_rev - base_rev, 0),
            "base_roi": round(base_roi, 2),
            "new_roi": round(new_roi, 2),
            "roi_change": round(new_roi - base_roi, 2)
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


def extract_json(text: str):
    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text)
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        return match.group(0).strip()
    return text


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_msg = data.get("message", "")

    from router import classify_intent
    intent = classify_intent(user_msg)

    if intent != "parse_budget":
        if intent == "analysis_question":
            prompt = f"""
            광고 성과 분석 전문가로서, 아래 질문을 광고 전략/ROI/예산 관점에서 답변하라.
            질문: {user_msg}
            """
            answer = smart_router(prompt, intent)
            return jsonify({"reply": answer.replace("\n", "<br>")})

        if intent == "general_chat":
            prompt = f"""
            너는 친절한 AI 비서이다.
            아래 메시지에 자연스럽고 인간적인 말투로 답하라.
            메시지: {user_msg}
            """
            answer = smart_router(prompt, intent)
            return jsonify({"reply": answer.replace("\n", "<br>")})

        return jsonify({"reply": "이해하지 못한 요청입니다. 광고/예산 관련 질문을 입력해주세요."})

    parsed_json = parse_user_input(user_msg)
    clean_json = extract_json(parsed_json)

    try:
        parsed = json.loads(clean_json)
    except:
        return jsonify({"reply": "JSON 파싱 오류\n" + parsed_json})

    base_search = float(parsed.get("기존 검색광고 예산", 0))
    base_live = float(parsed.get("기존 라이브광고 예산", 0))
    base_event = int(parsed.get("기존 프로모션 여부", 0))

    new_search = float(parsed.get("변동 검색광고 예산", 0))
    new_live = float(parsed.get("변동 라이브광고 예산", 0))
    new_event = int(parsed.get("변동 프로모션 여부", 0))

    def calc(search_cost, live_cost, event_flag):
        revenue = (
            INTERCEPT
            + search_cost * SEARCH_COEFF
            + live_cost * LIVE_COEFF
            + event_flag * EVENT_COEFF
        )
        total = search_cost + live_cost
        roi = (revenue - total) / (total if total > 0 else 1)
        return revenue, roi

    base_rev, base_roi = calc(base_search, base_live, base_event)
    new_rev, new_roi = calc(new_search, new_live, new_event)

    rev_change = new_rev - base_rev
    roi_change = new_roi - base_roi

    sim_url = url_for(
        'chat_simulate',
        base_search=base_search,
        base_live=base_live,
        base_event=base_event,
        new_search=new_search,
        new_live=new_live,
        new_event=new_event
    )

    T = "&nbsp;" * 5

    reply = f"""
        예산 시뮬레이션 결과<br><br>
        ■ 총 예산: {parsed.get('총 예산', 0):,}원<br><br>
        ■ 기존 예산<br>
        {T}검색광고: {base_search:,.0f}원<br>
        {T}라이브광고: {base_live:,.0f}원<br>
        프로모션: {'YES' if base_event else 'NO'}<br><br>
        ■ 변경 예산<br>
        {T}검색광고: {new_search:,.0f}원<br>
        {T}라이브광고: {new_live:,.0f}원<br>
        프로모션: {'YES' if new_event else 'NO'}<br><br>
        ■ 매출 변화: {rev_change:,.0f}원<br>
        ■ ROI 변화: {roi_change:.2f}<br><br>
        <a href="{sim_url}" target="_blank">시뮬레이션 화면으로 이동</a>
    """

    return jsonify({"reply": reply})


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


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html",
                           day_chart=day_chart,
                           promo_chart=promo_chart)


@app.route("/chat-simulate")
def chat_simulate():
    base_search = request.args.get("base_search", type=float, default=0)
    base_live = request.args.get("base_live", type=float, default=0)
    new_search = request.args.get("new_search", type=float, default=0)
    new_live = request.args.get("new_live", type=float, default=0)
    base_event = request.args.get("base_event", type=int, default=0)
    new_event = request.args.get("new_event", type=int, default=0)

    def calc(search_cost, live_cost, event_flag):
        revenue = (
            INTERCEPT
            + search_cost * SEARCH_COEFF
            + live_cost * LIVE_COEFF
            + event_flag * EVENT_COEFF
        )
        total = search_cost + live_cost
        roi = (revenue - total) / (total if total > 0 else 1)
        return revenue, roi

    base_rev, base_roi = calc(base_search, base_live, base_event)
    new_rev, new_roi = calc(new_search, new_live, new_event)

    return render_template(
        "chat_simulate.html",
        base_revenue=round(base_rev, 0),
        new_revenue=round(new_rev, 0),
        revenue_change=round(new_rev - base_rev, 0),
        base_roi=round(base_roi, 2),
        new_roi=round(new_roi, 2),
        roi_change=round(new_roi - base_roi, 2),
        base_search=base_search,
        base_live=base_live,
        new_search=new_search,
        new_live=new_live,
        promo_flag_base=base_event,
        promo_flag_new=new_event,
        INTERCEPT=INTERCEPT,
        SEARCH_COEFF=SEARCH_COEFF,
        LIVE_COEFF=LIVE_COEFF,
        EVENT_COEFF=EVENT_COEFF
    )


if __name__ == "__main__":
    app.run(debug=True)
