from flask import Flask, render_template
import plotly.express as px
import pandas as pd

app = Flask(__name__)

# 예시 데이터 (원래 형태 유지)
data_day = {
    '요일': ['월', '화', '수', '목', '금', '토', '일'] * 3,
    '시청자수': [18, 28, 51, 50, 29, 13, 6,
                11, 17, 17, 13, 11, 0, 0,
                2, 19, 18, 18, 28, 0, 0],
    '카테고리': ['B'] * 7 + ['D'] * 7 + ['L'] * 7
}
df_day = pd.DataFrame(data_day)

# 요일별 시청자 수
fig_day = px.bar(df_day, x='요일', y='시청자수', color='카테고리',
                 color_discrete_map={'B': '#9BE8D8', 'D': '#FFA87E', 'L': '#A1E2A1'},
                 barmode='group',
                 title='요일 및 카테고리별 평균 시청자 수')

day_chart = fig_day.to_html(full_html=False)

# 프로모션별 시청자 수
data_promo = {
    '프로모션': ['진행', '진행', '없음', '없음', '진행', '없음'],
    '시청자수': [60, 30, 10, 5, 40, 15],
    '카테고리': ['B', 'D', 'L', 'D', 'L', 'B']
}
df_promo = pd.DataFrame(data_promo)

fig_promo = px.box(df_promo, x='프로모션', y='시청자수', color='카테고리',
                   color_discrete_map={'B': '#9BE8D8', 'D': '#FFA87E', 'L': '#A1E2A1'},
                   title='프로모션 진행 여부에 따른 시청자 수 비교')

promo_chart = fig_promo.to_html(full_html=False)


@app.route('/')
def index():
    return render_template('index.html',
                           day_chart=day_chart,
                           promo_chart=promo_chart)


if __name__ == '__main__':
    app.run(debug=True)
