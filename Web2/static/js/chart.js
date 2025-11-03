// =========================
// AMMO Dashboard Chart Script
// =========================

document.addEventListener("DOMContentLoaded", () => {
  loadSearchData();
});
document.getElementById('applySimulation').addEventListener('click', runSimulation);

// -----------------------------
// 검색광고 실데이터 시각화
// -----------------------------
async function loadSearchData() {
  const response = await fetch('/data/search_volume');
  const text = await response.text();

  let delimiter = ',';
  if (text.includes('\t')) delimiter = '\t';
  else if (text.includes(';')) delimiter = ';';

  const rows = text.trim().split('\n').map(r => r.split(delimiter));
  const header = rows[0].map(h => h.trim());

  const brandIdx = header.indexOf('brand');
  const dateIdx = header.indexOf('date');
  const relIdx = header.indexOf('search_volume_relative');
  const cpcIdx = header.indexOf('cpc_est');
  const adIdx = header.indexOf('ad_spend_est');

  if (brandIdx === -1 || dateIdx === -1 || relIdx === -1) return;

  const data = rows.slice(1)
    .filter(r => r.length > 1)
    .map(r => ({
      brand: r[brandIdx],
      date: r[dateIdx],
      rel: parseFloat(r[relIdx]),
      cpc: parseFloat(r[cpcIdx]),
      ad: parseFloat(r[adIdx])
    }))
    .filter(d => !isNaN(d.rel));

  const brands = [...new Set(data.map(d => d.brand))];
  const brandColors = ['#0077b6', '#ff7f51', '#2ec4b6', '#8338ec', '#ffbe0b'];

  // 1. 상대적 검색량 추이
  const trendTraces = brands.map((b, i) => ({
    x: data.filter(d => d.brand === b).map(d => d.date),
    y: data.filter(d => d.brand === b).map(d => d.rel),
    name: b,
    type: 'scatter',
    line: { width: 2.5, color: brandColors[i % brandColors.length] }
  }));
  Plotly.newPlot('trend', trendTraces, commonLayout());

  // 2. 검색 점유율 변화
  const dates = [...new Set(data.map(d => d.date))];
  const shareData = dates.map(date => {
    const dayData = data.filter(d => d.date === date);
    const total = dayData.reduce((s, d) => s + d.rel, 0);
    const shares = {};
    brands.forEach(b => {
      const val = dayData.find(d => d.brand === b)?.rel || 0;
      shares[b] = total ? (val / total) * 100 : 0;
    });
    return { date, ...shares };
  });

  const shareTraces = brands.map((b, i) => ({
    x: shareData.map(d => d.date),
    y: shareData.map(d => d[b]),
    name: b,
    type: 'scatter',
    mode: 'lines',
    line: { width: 2, color: brandColors[i % brandColors.length] }
  }));
  Plotly.newPlot('share', shareTraces, commonLayout());

  // 3. CPC 추이
  const cpcTraces = brands.map((b, i) => ({
    x: data.filter(d => d.brand === b).map(d => d.date),
    y: data.filter(d => d.brand === b).map(d => d.cpc),
    name: b,
    type: 'scatter',
    line: { width: 2, color: brandColors[i % brandColors.length] }
  }));
  Plotly.newPlot('gender', cpcTraces, commonLayout());

  // 4. 광고비 추이
  const adTraces = brands.map((b, i) => ({
    x: data.filter(d => d.brand === b).map(d => d.date),
    y: data.filter(d => d.brand === b).map(d => d.ad),
    name: b,
    type: 'bar',
    marker: { color: brandColors[i % brandColors.length] }
  }));
  Plotly.newPlot('age', adTraces, {
    ...commonLayout(),
    barmode: 'group'
  });

  // 5. 월별/연도별 평균 검색량 히트맵
  try {
    const parsed = data.map(d => {
      const parts = d.date.includes('-')
        ? d.date.split('-')
        : [String(d.date).slice(0, 4), String(d.date).slice(4, 6)];
      return { year: parts[0], month: parts[1], value: d.rel };
    });
    const years = [...new Set(parsed.map(d => d.year))].sort();
    const months = ['01','02','03','04','05','06','07','08','09','10','11','12'];
    const z = years.map(y =>
      months.map(m => {
        const vals = parsed.filter(d => d.year === y && d.month === m).map(d => d.value);
        return vals.length ? vals.reduce((a,b)=>a+b,0)/vals.length : null;
      })
    );

    Plotly.newPlot('heat_b', [{
      z: z,
      x: months.map(m => m + '월'),
      y: years,
      type: 'heatmap',
      colorscale: 'Viridis'
    }], commonLayout());
  } catch (e) {
    console.error('히트맵 생성 오류:', e);
  }
}

function commonLayout() {
  return {
    legend: { orientation: 'h' },
    margin: { t: 30, l: 50, r: 30, b: 50 },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)'
  };
}

// 그래프 초기화
let simData = {
  x: [],
  revenue: [],
  roi: []
};

Plotly.newPlot('simChart', [
  {
    x: simData.x,
    y: simData.revenue,
    name: '예상 매출액',
    type: 'scatter',
    mode: 'lines+markers',
    line: { color: '#0077b6', width: 3 },
    marker: { size: 8 },
    yaxis: 'y1',
    text: [],
    hoverinfo: 'x+y+text'
  },
  {
    x: simData.x,
    y: simData.roi,
    name: '예상 ROI',
    type: 'scatter',
    mode: 'lines+markers',
    line: { color: '#0f9d58', width: 3 },
    marker: { size: 8 },
    yaxis: 'y2',
    text: [],
    hoverinfo: 'x+y+text'
  }
], {
  margin: { t: 30, l: 60, r: 60, b: 60 },
  paper_bgcolor: 'rgba(0,0,0,0)',
  plot_bgcolor: 'rgba(0,0,0,0)',
  xaxis: { title: '단계' },
  yaxis: { title: '예상 매출액 (원)', side: 'left', showgrid: true },
  yaxis2: { title: '예상 ROI', side: 'right', overlaying: 'y', showgrid: false },
  legend: { orientation: 'h' }
}, { responsive: true });

// -----------------------------
// ROI 시뮬레이션 실행
// -----------------------------
async function runSimulation() {
  try {
    const warningEl = document.getElementById('simulation-warning');
    warningEl.style.display = 'none'; // 초기화

    // 입력값 수집
    const baseSearch = document.getElementById('baseSearchAdCost').value;
    const baseLive = document.getElementById('baseLiveAdCost').value;
    const newSearch = document.getElementById('newSearchAdCost').value;
    const newLive = document.getElementById('newLiveAdCost').value;

    // 모든 칸에 값이 있는지 확인
    if (!baseSearch || !baseLive || !newSearch || !newLive) {
      warningEl.textContent = "모든 광고비 입력을 완료해주세요.";
      warningEl.style.display = 'block';
      return; // 서버 요청 중단
    }

    const payload = {
      base_search_ad_cost: parseFloat(document.getElementById('baseSearchAdCost').value) || 0,
      base_live_ad_cost: parseFloat(document.getElementById('baseLiveAdCost').value) || 0,
      base_competitor_event: document.getElementById('baseCompetitorEvent').value,
      new_search_ad_cost: parseFloat(document.getElementById('newSearchAdCost').value) || 0,
      new_live_ad_cost: parseFloat(document.getElementById('newLiveAdCost').value) || 0,
      new_competitor_event: document.getElementById('newCompetitorEvent').value
    };

    // 서버 요청
    const res = await fetch('/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const r = await res.json();
    if (!r.success) return;

    // 결과 표시
    document.getElementById('result-revenue').innerHTML =
      `<b style="color:#0077b6">${Number(r.new_revenue).toLocaleString()} 원</b>`;
    document.getElementById('result-revenue-change').innerHTML =
      `<b style="color:${r.revenue_change >= 0 ? '#2ec4b6' : '#ff9f1c'}">
        ${r.revenue_change >= 0 ? '+' : ''}${Number(r.revenue_change).toLocaleString()} 원</b>`;

    document.getElementById('result-roi').innerHTML =
      `<b style="color:#0f9d58">${Number(r.new_roi).toFixed(2)}</b>`;
    document.getElementById('result-roi-change').innerHTML =
      `<b style="color:${r.roi_change >= 0 ? '#2ec4b6' : '#ff9f1c'}">
        ${r.roi_change >= 0 ? '+' : ''}${Number(r.roi_change).toFixed(2)}</b>`;

    // x 좌표 추가
    const nextIndex = simData.x.length + 1;

    // 맨 처음 적용 시 기존값도 함께 추가
    if (simData.x.length === 0) {
      // 기존 값
      simData.x.push(0);  // 첫 번째 단계: 0
      simData.revenue.push(Number(r.base_revenue));
      simData.roi.push(Number(r.base_roi));
    }

    // 변동값 추가
    simData.x.push(nextIndex);
    simData.revenue.push(Number(r.new_revenue));
    simData.roi.push(Number(r.new_roi));

    // 그래프 업데이트
    Plotly.update('simChart', {
      x: [simData.x, simData.x],
      y: [simData.revenue, simData.roi]
    });


  } catch (e) {
    console.error('runSimulation() 오류:', e);
  }
}

// =========================
//  보고서 생성 버튼
// =========================
// =========================
//  보고서 생성 (수정본)
// =========================
async function generateReport(event) {
  const btn = event?.target || document.querySelector('.btn-generate');
  btn.disabled = true;
  btn.innerText = "생성 중...";

  try {
    const baseSearch = parseFloat(document.getElementById('baseSearchAdCost').value) || 0;
    const baseLive   = parseFloat(document.getElementById('baseLiveAdCost').value) || 0;
    const newSearch  = parseFloat(document.getElementById('newSearchAdCost').value) || 0;
    const newLive    = parseFloat(document.getElementById('newLiveAdCost').value) || 0;

    // 이벤트는 변동 기준으로 사용(원하면 base로 바꿔도 됨)
    const promo = document.getElementById('newCompetitorEvent').value; // 'Y' | 'N'

    const payload = {
      base_search_ad_cost: baseSearch,
      base_live_ad_cost:   baseLive,
      new_search_ad_cost:  newSearch,
      new_live_ad_cost:    newLive,
      competitor_event:    promo
    };

    const res = await fetch('/generate_report', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const r = await res.json();
    if (!r.success) throw new Error(r.message || "Unknown error");

    // PDF 즉시 다운로드
    const a = document.createElement("a");
    a.href = r.download_url;
    a.download = "report.pdf";
    document.body.appendChild(a);
    a.click();
    a.remove();
  } catch (err) {
    alert("보고서 생성 실패: " + err.message);
    console.error(err);
  } finally {
    btn.disabled = false;
    btn.innerText = "보고서 생성";
  }
}

