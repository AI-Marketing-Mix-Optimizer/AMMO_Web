// =========================
// ✅ 탭 전환 기능
// =========================
function showTab(tabId) {
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(tabId).classList.add('active');
    document.querySelector(`.tab-btn[onclick="showTab('${tabId}')"]`).classList.add('active');
}

// =========================
// ⚙️ 공통 Plotly 애니메이션 설정
// =========================
const animationConfig = {
    transition: { duration: 800, easing: 'cubic-in-out' },
    frame: { duration: 500, redraw: false }
};

// =========================
// 🔍 검색광고 섹션
// =========================

// (1) 상대적 검색량 추이
Plotly.newPlot('trend', [
    {x:['2018','2019','2020','2021','2022','2023','2024'], y:[1,2,3,4,4,3,2], name:'비엔날씬', type:'scatter', line:{color:'#8BC34A', width:4}},
    {x:['2018','2019','2020','2021','2022','2023','2024'], y:[3,5,8,10,8,7,9], name:'덴마크 유산균이야기', type:'scatter', line:{color:'#4FC3F7', width:4}},
    {x:['2018','2019','2020','2021','2022','2023','2024'], y:[2,4,9,5,3,2,1], name:'락토핏', type:'scatter', line:{color:'#FFB74D', width:4}}
], {
    title:'브랜드별 상대적 검색량 추이',
    legend:{orientation:'h'},
    paper_bgcolor:'rgba(0,0,0,0)',
    plot_bgcolor:'rgba(0,0,0,0)',
    yaxis:{range:[0,12]}
}).then(g => Plotly.animate(g, null, animationConfig));


// (2) 검색 점유율 변화
Plotly.newPlot('share', [
    {x:['2018','2019','2020','2021','2022','2023','2024'], y:[20,25,30,40,45,50,55], name:'덴마크', type:'scatter', fill:'tonexty', line:{color:'#4FC3F7'}},
    {x:['2018','2019','2020','2021','2022','2023','2024'], y:[60,55,50,45,40,35,30], name:'락토핏', type:'scatter', fill:'tonexty', line:{color:'#FFB74D'}},
    {x:['2018','2019','2020','2021','2022','2023','2024'], y:[20,20,20,15,15,15,15], name:'비엔날씬', type:'scatter', fill:'tonexty', line:{color:'#8BC34A'}}
], {
    title:'브랜드별 검색 점유율 변화 (%)',
    legend:{orientation:'h'},
    paper_bgcolor:'rgba(0,0,0,0)',
    plot_bgcolor:'rgba(0,0,0,0)',
}).then(g => Plotly.animate(g, null, animationConfig));


// (3) 성별 검색량 추이 (민트/오렌지)
Plotly.newPlot('gender', [
    {x:['2018','2019','2020','2021','2022','2023','2024'], y:[10,20,25,28,26,30,32], name:'남성', type:'scatter', line:{color:'#00E6B3', width:4}},
    {x:['2018','2019','2020','2021','2022','2023','2024'], y:[20,30,35,40,42,45,50], name:'여성', type:'scatter', line:{color:'#FFA94D', width:4}}
], {
    title:'성별에 따른 검색량 추이',
    legend:{orientation:'h'},
    paper_bgcolor:'rgba(0,0,0,0)',
    plot_bgcolor:'rgba(0,0,0,0)',
}).then(g => Plotly.animate(g, null, animationConfig));


// (4) 연령대별 검색량 비교
Plotly.newPlot('age', [
    {x:['18세 이하','19-39세','40-59세','60세 이상'], y:[3.4,12.8,5.6,2.0], name:'덴마크', type:'bar', marker:{color:'#4FC3F7'}},
    {x:['18세 이하','19-39세','40-59세','60세 이상'], y:[3.7,16.5,4.0,1.6], name:'락토핏', type:'bar', marker:{color:'#FFB74D'}},
    {x:['18세 이하','19-39세','40-59세','60세 이상'], y:[0.6,1.7,0.7,0.2], name:'비엔날씬', type:'bar', marker:{color:'#8BC34A'}}
], {
    barmode:'group',
    title:'연령대별 브랜드 평균 검색량 비교',
    legend:{orientation:'h'},
    paper_bgcolor:'rgba(0,0,0,0)',
    plot_bgcolor:'rgba(0,0,0,0)',
    yaxis:{range:[0,18]}
}).then(g => Plotly.animate(g, null, animationConfig));


// (5) 히트맵 예시
let heatData = {
    z: [
        [0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0.2,0.3,0.2],
        [0.2,0.2,0.3,1.5,1.4,0.9,1.0,1.3,1.7,1.0,0.7,0.7],
        [0.9,0.9,0.9,1.1,1.1,0.9,0.8,1.3,0.9,0.7,0.6,0.8],
        [1.2,1.1,0.9,1.1,1.1,1.3,1.0,1.1,1.0,0.7,0.7,0.7],
        [0.9,0.8,1.0,0.9,1.0,0.9,1.0,0.9,0.8,0.8,0.7,0.8],
        [0.9,0.9,0.9,1.0,1.0,1.0,0.9,0.8,0.9,0.9,0.9,0.8],
    ],
    x:['1','2','3','4','5','6','7','8','9','10','11','12'],
    y:['2018','2019','2020','2021','2022','2023','2024'],
    type:'heatmap',
    colorscale:'Viridis'
};
Plotly.newPlot('heat_b', [heatData], {
    title:'[비엔날씬] 월별/연도별 평균 검색량',
    paper_bgcolor:'rgba(0,0,0,0)',
    plot_bgcolor:'rgba(0,0,0,0)'
}).then(g => Plotly.animate(g, null, animationConfig));


// =========================
// 🎥 쇼핑라이브 섹션
// =========================

// 자동 통계 계산 (임의 값)
let data_live = {
    totalVideos: 182,
    totalComments: 225564,
    avgDuration: 4963
};

// 요약 카드 표시
const cards = document.querySelectorAll('.summary-card');
cards[0].innerHTML = `<h3>총 영상 수</h3><p><b>${data_live.totalVideos.toLocaleString()}개</b></p>`;
cards[1].innerHTML = `<h3>총 댓글 수</h3><p><b>${data_live.totalComments.toLocaleString()}개</b></p>`;
cards[2].innerHTML = `<h3>평균 영상 시간</h3><p><b>${data_live.avgDuration.toLocaleString()}초</b></p>`;

// (1) 요일별 평균 시청자 수
Plotly.newPlot('weekday', [
    {x:['월','화','수','목','금','토','일'], y:[2.0,28.3,50.9,51.0,28.7,13.3,6.1], name:'B', type:'bar', marker:{color:'#80DEEA'}},
    {x:['월','화','수','목','금','토','일'], y:[18.0,19.2,18.1,18.4,28.7,13.3,6.1], name:'L', type:'bar', marker:{color:'#A5D6A7'}},
    {x:['월','화','수','목','금','토','일'], y:[11.3,16.9,17.4,12.9,11.2,0.7,0.7], name:'D', type:'bar', marker:{color:'#F8BBD0'}}
], {
    barmode:'group',
    title:'요일 및 카테고리별 평균 시청자 수',
    legend:{orientation:'h'},
    paper_bgcolor:'rgba(0,0,0,0)',
    plot_bgcolor:'rgba(0,0,0,0)'
}).then(g => Plotly.animate(g, null, animationConfig));

// (2) 프로모션 여부별 시청자 수 비교
Plotly.newPlot('promotion', [
    {y:[60,35,10], x:['프로모션 진행','프로모션 진행','프로모션 없음'], name:'B', type:'box', marker:{color:'#80DEEA'}},
    {y:[30,18,12], x:['프로모션 진행','프로모션 진행','프로모션 없음'], name:'D', type:'box', marker:{color:'#F8BBD0'}},
    {y:[35,36,10], x:['프로모션 진행','프로모션 진행','프로모션 없음'], name:'L', type:'box', marker:{color:'#A5D6A7'}}
], {
    title:'프로모션 진행 여부에 따른 시청자 수 비교',
    boxmode:'group',
    paper_bgcolor:'rgba(0,0,0,0)',
    plot_bgcolor:'rgba(0,0,0,0)'
}).then(g => Plotly.animate(g, null, animationConfig));
