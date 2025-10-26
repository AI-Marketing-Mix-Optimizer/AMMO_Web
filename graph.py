import plotly.graph_objects as go

# 데이터 입력
features = ['검색광고 (β₁)', '라이브광고 (β₂)', '경쟁사이벤트 (β₃)']
values = [923318306.5, 571964471.5, 429519758.1]

# 그래프 생성 (막대 위 숫자 제거)
fig = go.Figure(
    data=[go.Bar(
        x=features,
        y=values,
        marker_color=['#2E86DE', '#28B463', '#E74C3C'],
        width=0.45
    )]
)

# 레이아웃 설정
fig.update_layout(
    title=dict(
        text='ROI 기여도 막대그래프 (β₁, β₂, β₃ 비교)',
        font=dict(size=48, color='black')
    ),
    yaxis=dict(
        title='beta_scaled (log scale)',
        type='linear',
        tickvals=[4.0e8, 5.0e8, 6.0e8, 7.0e8, 8.0e8, 9.0e8, 1.0e9],
        ticktext=['400M', '500M', '600M', '700M', '800M', '900M', '950M'],
        showgrid=True,
        gridcolor='rgba(200,200,200,0.3)',
        zeroline=False,
        titlefont=dict(size=36),
        tickfont=dict(size=32)
    ),
    xaxis=dict(
        tickfont=dict(size=36)
    ),
    plot_bgcolor='rgba(0,0,0,0)',   # 배경 투명
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(size=34, color='black'),
    bargap=0.5,
    width=2300,   # 가로비율 더 넓게
    height=650    # 세로비율 납작하게
)

fig.show()

# 필요 시 PPT용 투명 PNG 저장
# fig.write_image("roi_bar_chart_clean.png", scale=4, width=2300, height=650, engine="kaleido")
