# ============================================
#  report_gen.py
# ============================================
import os, json
from datetime import datetime
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import numpy as np

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.utils import ImageReader

from dotenv import load_dotenv
from openai import OpenAI

# -------- INIT --------
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MALGUN = r"C:\Windows\Fonts\malgun.ttf"
if os.path.exists(MALGUN):
    pdfmetrics.registerFont(TTFont("Malgun", MALGUN))
    matplotlib.rcParams["font.family"] = ["Malgun Gothic"]

matplotlib.rcParams["axes.unicode_minus"] = False

PAGE_W, PAGE_H = A4
LM, RM, TM, BM = 70, 50, 60, 60
CONTENT_W = PAGE_W - LM - RM

# -------- 계산 함수 --------
def calc_revenue_roi(search, live, event, coeffs):
    revenue = (
        coeffs["BETA_0"]
        + coeffs["BETA_SEARCH"] * search
        + coeffs["BETA_LIVE"] * live
        + coeffs["BETA_EVENT"] * event
    )
    cost = search + live
    roi = (revenue - cost) / (cost if cost > 0 else 1)
    return revenue, roi

# -------- 그래프 --------
def save_sim_line_chart(base_s, base_l, target_s, target_l, event, coeffs, compare_s=None, compare_l=None):
    ratios = np.linspace(0, 1, 6)
    revs_main, rois_main = [], []
    revs_compare = []

    for r in ratios:
        s = base_s + (target_s - base_s) * r
        l = base_l + (target_l - base_l) * r
        rev, roi = calc_revenue_roi(s, l, event, coeffs)
        revs_main.append(rev)
        rois_main.append(roi)

        if compare_s is not None:
            s2 = base_s + (compare_s - base_s) * r
            l2 = base_l + (compare_l - base_l) * r
            rev2, _ = calc_revenue_roi(s2, l2, event, coeffs)
            revs_compare.append(rev2)

    fig, ax1 = plt.subplots(figsize=(6.4, 3.2), dpi=300)

    # 매출 라인 (파랑)
    ax1.plot(ratios, revs_main, linewidth=3, color="#0077b6", label="예상 매출")

    # 비교선
    if compare_s is not None:
        ax1.plot(ratios, revs_compare, linewidth=3, color="#0077b6", label="AI 예상 매출")

    # ROI 라인 (초록)
    ax2 = ax1.twinx()
    ax2.plot(ratios, rois_main, linewidth=3, color="#0f9d58", label="ROI")

    # Y축 단위 B원 (십억 단위) 유지
    ax1.set_ylabel("예상 매출 (B원)", color="#0077b6")
    ax1.get_yaxis().set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, _: f"{x/1e9:.1f}B")
    )
    ax2.set_ylabel("ROI", color="#0f9d58")

    # 스타일
    ax1.set_xticks(ratios)
    ax1.grid(True, linestyle="--", alpha=0.4)
    plt.title("예산 변화 시뮬레이션")

    fig.tight_layout()
    buf = io.BytesIO()
    FigureCanvas(fig).print_png(buf)
    plt.close(fig)
    buf.seek(0)
    return buf

# -------- LLM 비율 추천 --------
def call_llm_for_ratio(total, coeffs):
    prompt = f"""
총 {total:,}원을 검색/라이브에 배분해 ROI를 극대화.
한국형 비즈니스 톤. JSON ONLY.

예시 출력:
{{
  "search_ratio": 0.55,
  "live_ratio": 0.45,
  "insight_title": "예산 재배분 근거",
  "insight_bullets": ["검색 초기 효율 우위","라이브 효율 감소 구간"],
  "notes": "균형형 전략"
}}
"""
    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[{"role":"user","content":prompt}]
        )
        raw = r.choices[0].message.content

        # JSON 부분만 추출
        start = raw.find("{")
        end = raw.rfind("}") + 1
        json_str = raw[start:end]

        js = json.loads(json_str)

        s, l = js["search_ratio"], js["live_ratio"]
        s, l = s/(s+l), l/(s+l)

        # Python3.8 호환 (딕셔너리 머지)
        js["s"], js["l"] = s, l
        return js

    except Exception as e:
        print("LLM ratio parse error:", e)
        return {
            "s":0.5, "l":0.5,
            "insight_title":"기본전략",
            "insight_bullets":["백업값 사용"],
            "notes":"-"
        }

# -------- 테이블 utils --------
def draw_table(c, data, y):
    col_width = (CONTENT_W-20) / len(data[0])
    t = Table(data, colWidths=[col_width]*len(data[0]))
    t.setStyle(TableStyle([
        ("FONTNAME",(0,0),(-1,-1),"Malgun"),
        ("GRID",(0,0),(-1,-1),0.7,colors.grey),
        ("BACKGROUND",(0,0),(-1,0),colors.lightgrey),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("FONTSIZE",(0,0),(-1,-1),10)
    ]))
    w,h = t.wrapOn(c, CONTENT_W, y)
    if y-h < 100:
        c.showPage(); y = PAGE_H - 80
    t.drawOn(c, LM, y-h)
    return y-h-25

def add_section_title(c, y, text):
    c.setFont("Malgun",13)
    c.drawString(LM, y, text)
    y -= 10
    c.setLineWidth(1)
    c.line(LM, y, PAGE_W-RM, y)
    return y-20

# -------- MAIN --------
def generate_llm_report(base_s, base_l, promo_flag, coeffs, out_dir, new_s, new_l):
    os.makedirs(out_dir, exist_ok=True)
    pdf = os.path.join(out_dir, f"report_{datetime.now():%Y%m%d_%H%M%S}.pdf")

    event = 1 if promo_flag else 0

    base_rev, base_roi = calc_revenue_roi(base_s, base_l, event, coeffs)
    new_rev, new_roi   = calc_revenue_roi(new_s, new_l, event, coeffs)

    # AI 추천 기준 = 변동 예산 총액
    change_total = new_s + new_l
    js = call_llm_for_ratio(change_total, coeffs)

    ai_s = change_total * js["s"]
    ai_l = change_total * js["l"]
    ai_rev, ai_roi = calc_revenue_roi(ai_s, ai_l, event, coeffs)

    # 그래프 저장
    user_chart_buf = save_sim_line_chart(base_s, base_l, new_s, new_l, event, coeffs)
    ai_chart_buf = save_sim_line_chart(base_s, base_l, ai_s, ai_l, event, coeffs, compare_s=ai_s, compare_l=ai_l)

    c = canvas.Canvas(pdf, pagesize=A4)
    y = PAGE_H - 60

    # HEADER
    c.setFont("Malgun",18)
    c.drawCentredString(PAGE_W/2, y, "광고 예산 최적화 리포트")
    y -= 40

    # 1. 사용자 입력
    y = add_section_title(c, y, "1. 사용자 입력 요약")
    info = [
        ["구분","검색","라이브","경쟁사 이벤트"],
        ["기존 광고비", f"{base_s:,.0f}원", f"{base_l:,.0f}원", "있음" if promo_flag else "없음"],
        ["변동 광고비", f"{new_s:,.0f}원", f"{new_l:,.0f}원", "있음" if promo_flag else "없음"]
    ]
    y = draw_table(c, info, y)

    # 2. 계수 표
    y = add_section_title(c, y, "2. 사용된 회귀계수")
    data_coeff = [
        ["계수","값"],
        ["Intercept", f"{coeffs['BETA_0']:,.4f}"],
        ["검색 효과", f"{coeffs['BETA_SEARCH']:,.8f}"],
        ["라이브 효과", f"{coeffs['BETA_LIVE']:,.8f}"],
        ["이벤트 효과", f"{coeffs['BETA_EVENT']:,.8f}"]
    ]
    y = draw_table(c, data_coeff, y)

    # 3. 사용자 결과
    y = add_section_title(c, y, "3. 사용자 시뮬레이션 결과")
    metrics = [
        ["항목","값"],
        ["예상 매출액", f"{new_rev:,.0f}원"],
        ["예상 ROI", f"{new_roi:.2f}"],
        ["예상 매출 변화량", f"{new_rev-base_rev:,.0f}원"],
        ["예상 ROI 변화량", f"{new_roi-base_roi:.2f}"]
    ]
    y = draw_table(c, metrics, y)

    if y < 300:
        c.showPage(); y = PAGE_H - 60

    c.drawString(LM, y, "예상 변화 그래프 (사용자)")
    y -= 5
    c.drawImage(ImageReader(user_chart_buf), LM, y-230, width=CONTENT_W-30, height=200)
    y -= 300

    #  NEW PAGE FOR AI SECTION
    c.showPage()
    y = PAGE_H - 60

    # 4. AI 추천
    y = add_section_title(c, y, "4. AI 추천 예산안")

    ai_data = [
        ["구분","검색","라이브","총액","예상 매출","ROI"],
        ["기존 광고비", f"{base_s:,.0f}원", f"{base_l:,.0f}원", f"{base_s+base_l:,.0f}원", f"{base_rev:,.0f}원", f"{base_roi:.2f}"],
        ["변동 광고비", f"{new_s:,.0f}원", f"{new_l:,.0f}원", f"{change_total:,.0f}원", f"{new_rev:,.0f}원", f"{new_roi:.2f}"],
        ["AI 추천", f"{ai_s:,.0f}원", f"{ai_l:,.0f}원", f"{ai_s+ai_l:,.0f}원", f"{ai_rev:,.0f}원", f"{ai_roi:.2f}"],
    ]

    #  개별 컬럼 폭 설정
    col_widths = [
        70,   # 구분
        80,   # 검색
        80,   # 라이브
        80,   # 총액
        100,  # 예상 매출
        60    # ROI
    ]

    t = Table(ai_data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("FONTNAME",(0,0),(-1,-1),"Malgun"),
        ("GRID",(0,0),(-1,-1),0.7,colors.grey),
        ("BACKGROUND",(0,0),(-1,0),colors.lightgrey),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("FONTSIZE",(0,0),(-1,-1),10)
    ]))

    w,h = t.wrapOn(c, CONTENT_W, y)
    if y-h < 100:
        c.showPage()
        y = PAGE_H - 80
    t.drawOn(c, LM, y-h)
    y = y-h-25
    
    # AI 그래프
    c.drawString(LM, y, "AI 예산 시뮬레이션 그래프")
    y -= 15
    c.drawImage(ImageReader(ai_chart_buf), LM, y-230, width=CONTENT_W-30, height=200)
    y -= 260

    # 5. 인사이트
    y = add_section_title(c, y, "5. 인사이트 요약")
    c.setFont("Malgun",11)
    c.drawString(LM, y, f" {js['insight_title']}")
    y -= 18

    c.setFont("Malgun",10)
    for b in js["insight_bullets"]:
        c.drawString(LM+10, y, f"- {b}")
        y -= 14

    y -= 10
    c.drawString(LM, y, f" Summary: {js['notes']}")
    c.save()

    return pdf
