// =========================
// AMMO Dashboard Chart Script
// =========================

document.addEventListener("DOMContentLoaded", () => {
  loadSearchData();
  setupSimulationListeners();
  runSimulation();
});

function setupSimulationListeners() {
  const inputs = ['searchAdCost', 'liveAdCost', 'competitorEvent'];
  inputs.forEach(id => {
    const element = document.getElementById(id);
    if (element) {
      element.addEventListener('change', runSimulation);
      element.addEventListener('input', runSimulation);
    }
  });
}

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

// -----------------------------
// ROI 시뮬레이션 실행
// -----------------------------
async function runSimulation() {
  try {
    const searchCostValue = document.getElementById('searchAdCost').value;
    const liveCostValue = document.getElementById('liveAdCost').value;

    const payload = {
      search_ad_cost: parseFloat(searchCostValue) || 0,
      live_ad_cost: parseFloat(liveCostValue) || 0,
      competitor_event: document.getElementById('competitorEvent').value
    };

    const res = await fetch('/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const r = await res.json();
    if (!r.success) return;

    document.getElementById('result-revenue').innerHTML =
      `<b style="color:#0077b6">${Number(r.revenue_change).toLocaleString()} 원</b>`;
    document.getElementById('result-roi').innerHTML =
      `<b style="color:#0f9d58">${Number(r.roi_change).toLocaleString()}</b>`;

    const labels = ['매출 변화량', 'ROI 변화량'];
    const values = [Number(r.revenue_change), Number(r.roi_change)];
    const maxVal = Math.max(...values, 0);
    const minVal = Math.min(...values, 0);
    const pad = Math.max(Math.abs(maxVal), Math.abs(minVal)) * 0.2;

    const trace = {
      x: labels,
      y: values,
      type: 'bar',
      marker: { color: values.map(v => v >= 0 ? '#2ec4b6' : '#ff9f1c') },
      text: values.map(v => v.toLocaleString()),
      textposition: 'outside',
      cliponaxis: false
    };

    const layout = {
      margin: { t: 30, l: 60, r: 30, b: 60 },
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
      yaxis: {
        title: '변화량',
        zeroline: true,
        zerolinecolor: '#333',
        range: [minVal - pad, maxVal + pad]
      },
      bargap: 0.3,
      showlegend: false,
      height: 420
    };

    Plotly.newPlot('simChart', [trace], layout, { responsive: true });
  } catch (e) {
    console.error('runSimulation() 오류:', e);
  }
}
