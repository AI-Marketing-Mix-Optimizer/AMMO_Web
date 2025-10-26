// =========================
// ✅ 탭 전환 (버튼 + 네비게이션 공통)
// =========================
function showTab(tabId) {
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
    document.getElementById(tabId).classList.add('active');
    const selector = `.nav-link[onclick="showTab('${tabId}')"]`;
    const activeLink = document.querySelector(selector);
    if (activeLink) activeLink.classList.add('active');
  }
  
  // =========================
  // 🔍 검색광고 실데이터 시각화
  // =========================
  async function loadSearchData() {
    console.log("✅ loadSearchData() 실행됨");
  
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
  
    if (brandIdx === -1 || dateIdx === -1 || relIdx === -1) {
      console.error('⚠️ CSV 헤더 구조 불일치:', header);
      return;
    }
  
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
    console.log('✅ 불러온 브랜드 목록:', brands);
  
    // === 색상 팔레트 (AMMO 톤 기반) ===
    const brandColors = [
      '#0077b6', // 블루
      '#ff7f51', // 오렌지
      '#2ec4b6', // 청록
      '#8338ec', // 퍼플
      '#ffbe0b'  // 옐로
    ];
  
    // === 1️⃣ 상대적 검색량 추이 ===
    const trendTraces = brands.map((b, i) => ({
      x: data.filter(d => d.brand === b).map(d => d.date),
      y: data.filter(d => d.brand === b).map(d => d.rel),
      name: b,
      type: 'scatter',
      line: { width: 2.5, color: brandColors[i % brandColors.length] }
    }));
    Plotly.newPlot('trend', trendTraces, {
      title: '브랜드별 상대적 검색량 추이',
      legend: { orientation: 'h' },
      margin: { t: 40, l: 50, r: 30 },
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)'
    });
  
    // === 2️⃣ 검색 점유율 변화 ===
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
      fill: 'none', // ✅ 면적 겹침 방지
      line: { width: 2, color: brandColors[i % brandColors.length] }
    }));
    Plotly.newPlot('share', shareTraces, {
      title: '브랜드별 검색 점유율 변화 (%)',
      legend: { orientation: 'h' },
      margin: { t: 40, l: 50, r: 30 },
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)'
    });
  
    // === 3️⃣ CPC 추이 ===
    const cpcTraces = brands.map((b, i) => ({
      x: data.filter(d => d.brand === b).map(d => d.date),
      y: data.filter(d => d.brand === b).map(d => d.cpc),
      name: b,
      type: 'scatter',
      line: { width: 2, color: brandColors[i % brandColors.length] }
    }));
    Plotly.newPlot('gender', cpcTraces, {
      title: '브랜드별 CPC 추이',
      legend: { orientation: 'h' },
      margin: { t: 40, l: 50, r: 30 },
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)'
    });
  
    // === 4️⃣ 광고비 추이 ===
    const adTraces = brands.map((b, i) => ({
      x: data.filter(d => d.brand === b).map(d => d.date),
      y: data.filter(d => d.brand === b).map(d => d.ad),
      name: b,
      type: 'bar',
      marker: { color: brandColors[i % brandColors.length] }
    }));
    Plotly.newPlot('age', adTraces, {
      title: '브랜드별 광고비 추이',
      legend: { orientation: 'h' },
      barmode: 'group',
      margin: { t: 40, l: 50, r: 30 },
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)'
    });
  
    // === 5️⃣ 히트맵 ===
    const parsed = data.map(d => {
      const [y, m] = d.date.split('-');
      return { year: y, month: m, value: d.rel };
    });
    const years = [...new Set(parsed.map(d => d.year))];
    const months = [...new Set(parsed.map(d => d.month))];
    const z = years.map(y =>
      months.map(m => {
        const vals = parsed.filter(d => d.year === y && d.month === m).map(d => d.value);
        return vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0;
      })
    );
  
    Plotly.newPlot('heat_b', [{
      z, x: months, y: years, type: 'heatmap', colorscale: 'Viridis'
    }], {
      title: '월별/연도별 평균 검색량',
      margin: { t: 40, l: 60, r: 30 },
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)'
    });
  }
  
  // ✅ 실행
  loadSearchData();
  
  // =========================
  // 🎥 쇼핑라이브 요약 카드
  // =========================
  let data_live = { totalVideos: 48, totalComments: 72566, avgDuration: 87.13 };
  document.getElementById('totalVideos').innerHTML = `<h3>총 영상 수</h3><p><b>${data_live.totalVideos.toLocaleString()}개</b></p>`;
  document.getElementById('totalComments').innerHTML = `<h3>총 댓글 수</h3><p><b>${data_live.totalComments.toLocaleString()}개</b></p>`;
  document.getElementById('avgDuration').innerHTML = `<h3>평균 영상 시간</h3><p><b>${data_live.avgDuration.toFixed(2)}분</b></p>`;
  
  // =========================
  // 💡 시뮬레이션 실행
  // =========================
  async function runSimulation() {
    const payload = {
      search_ad_cost: parseFloat(document.getElementById('searchAdCost').value) || 0,
      live_ad_cost: parseFloat(document.getElementById('liveAdCost').value) || 0,
      competitor_event: document.getElementById('competitorEvent').value
    };
  
    const res = await fetch('/simulate', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const r = await res.json();
    if (!r.success) return alert(r.message);
  
    document.getElementById('result-revenue').innerText = `${r.revenue_change.toLocaleString()} 원`;
    document.getElementById('result-roi').innerText = `${r.roi_change.toFixed(2)}`;
  
    Plotly.newPlot('simChart', [{
      x: ['매출 변화량', 'ROI 변화량'],
      y: [r.revenue_change, r.roi_change],
      type: 'bar',
      marker: { color: ['#2ec4b6', '#ff9f1c'] }
    }], {
      title: '시뮬레이션 결과 변화량',
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
      yaxis: { title: '변화량' }
    });
  }
  