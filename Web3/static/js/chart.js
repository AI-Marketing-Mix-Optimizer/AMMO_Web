// =========================
// AMMO Dashboard Chart Script
// =========================

document.addEventListener("DOMContentLoaded", () => {
  loadSearchData();

  // ✅ 챗봇 토글 이벤트 등록
  const toggleBtn = document.getElementById("chatbot-toggle");
  const chatWindow = document.getElementById("chatbot-window");

  if (toggleBtn && chatWindow) {
    toggleBtn.addEventListener("click", () => {
      chatWindow.style.display =
        chatWindow.style.display === "flex" ? "none" : "flex";
      chatWindow.style.flexDirection = "column";
    });
  }

  // ✅ 챗봇 메시지 전송
  const chatSend = document.getElementById("chatbot-send");
  const chatInput = document.getElementById("chatbot-text");
  const chatBody = document.getElementById("chatbot-body");

  async function sendMessage() {
    const msg = chatInput.value.trim();
    if (!msg) return;
    appendMessage("user", msg);
    chatInput.value = "";
    appendMessage("bot", "분석 중...");

    try {
      const res = await fetch("/chatbot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: msg }),
      });
      const data = await res.json();

      if (data.success) {
        chatBody.lastChild.textContent = `${data.summary}\n\nROI: ${data.result.new_roi} / 매출 변화: ${data.result.revenue_change.toLocaleString()}원`;
      } else {
        chatBody.lastChild.textContent = `⚠️ 오류: ${data.message}`;
      }
    } catch (e) {
      chatBody.lastChild.textContent = "⚠️ 서버 오류: " + e;
    }
  }

  function appendMessage(sender, text) {
    const msg = document.createElement("div");
    msg.classList.add("chatbot-message", `chatbot-${sender}`);
    msg.textContent = text;
    chatBody.appendChild(msg);
    chatBody.scrollTop = chatBody.scrollHeight;
  }

  if (chatSend && chatInput) {
    chatSend.addEventListener("click", sendMessage);
    chatInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") sendMessage();
    });
  }
});

document.getElementById("applySimulation").addEventListener("click", runSimulation);

// -----------------------------
// 검색광고 실데이터 시각화
// -----------------------------
async function loadSearchData() {
  const response = await fetch("/data/search_volume");
  const text = await response.text();

  let delimiter = ",";
  if (text.includes("\t")) delimiter = "\t";
  else if (text.includes(";")) delimiter = ";";

  const rows = text.trim().split("\n").map((r) => r.split(delimiter));
  const header = rows[0].map((h) => h.trim());

  const brandIdx = header.indexOf("brand");
  const dateIdx = header.indexOf("date");
  const relIdx = header.indexOf("search_volume_relative");
  const cpcIdx = header.indexOf("cpc_est");
  const adIdx = header.indexOf("ad_spend_est");

  if (brandIdx === -1 || dateIdx === -1 || relIdx === -1) return;

  const data = rows
    .slice(1)
    .filter((r) => r.length > 1)
    .map((r) => ({
      brand: r[brandIdx],
      date: r[dateIdx],
      rel: parseFloat(r[relIdx]),
      cpc: parseFloat(r[cpcIdx]),
      ad: parseFloat(r[adIdx]),
    }))
    .filter((d) => !isNaN(d.rel));

  const brands = [...new Set(data.map((d) => d.brand))];
  const brandColors = ["#0077b6", "#ff7f51", "#2ec4b6", "#8338ec", "#ffbe0b"];

  const trendTraces = brands.map((b, i) => ({
    x: data.filter((d) => d.brand === b).map((d) => d.date),
    y: data.filter((d) => d.brand === b).map((d) => d.rel),
    name: b,
    type: "scatter",
    line: { width: 2.5, color: brandColors[i % brandColors.length] },
  }));
  Plotly.newPlot("trend", trendTraces, commonLayout());

  const dates = [...new Set(data.map((d) => d.date))];
  const shareData = dates.map((date) => {
    const dayData = data.filter((d) => d.date === date);
    const total = dayData.reduce((s, d) => s + d.rel, 0);
    const shares = {};
    brands.forEach((b) => {
      const val = dayData.find((d) => d.brand === b)?.rel || 0;
      shares[b] = total ? (val / total) * 100 : 0;
    });
    return { date, ...shares };
  });

  const shareTraces = brands.map((b, i) => ({
    x: shareData.map((d) => d.date),
    y: shareData.map((d) => d[b]),
    name: b,
    type: "scatter",
    mode: "lines",
    line: { width: 2, color: brandColors[i % brandColors.length] },
  }));
  Plotly.newPlot("share", shareTraces, commonLayout());

  const cpcTraces = brands.map((b, i) => ({
    x: data.filter((d) => d.brand === b).map((d) => d.date),
    y: data.filter((d) => d.brand === b).map((d) => d.cpc),
    name: b,
    type: "scatter",
    line: { width: 2, color: brandColors[i % brandColors.length] },
  }));
  Plotly.newPlot("gender", cpcTraces, commonLayout());

  const adTraces = brands.map((b, i) => ({
    x: data.filter((d) => d.brand === b).map((d) => d.date),
    y: data.filter((d) => d.brand === b).map((d) => d.ad),
    name: b,
    type: "bar",
    marker: { color: brandColors[i % brandColors.length] },
  }));
  Plotly.newPlot("age", adTraces, {
    ...commonLayout(),
    barmode: "group",
  });

  try {
    const parsed = data.map((d) => {
      const parts = d.date.includes("-")
        ? d.date.split("-")
        : [String(d.date).slice(0, 4), String(d.date).slice(4, 6)];
      return { year: parts[0], month: parts[1], value: d.rel };
    });
    const years = [...new Set(parsed.map((d) => d.year))].sort();
    const months = [
      "01","02","03","04","05","06","07","08","09","10","11","12"
    ];
    const z = years.map((y) =>
      months.map((m) => {
        const vals = parsed
          .filter((d) => d.year === y && d.month === m)
          .map((d) => d.value);
        return vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : null;
      })
    );

    Plotly.newPlot(
      "heat_b",
      [
        {
          z: z,
          x: months.map((m) => m + "월"),
          y: years,
          type: "heatmap",
          colorscale: "Viridis",
        },
      ],
      commonLayout()
    );
  } catch (e) {
    console.error("히트맵 생성 오류:", e);
  }
}

function commonLayout() {
  return {
    legend: { orientation: "h" },
    margin: { t: 30, l: 50, r: 30, b: 50 },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
  };
}

// -----------------------------
// ROI 시뮬레이션 실행
// -----------------------------
let simData = { x: [], revenue: [], roi: [] };

async function runSimulation() {
  try {
    const warningEl = document.getElementById("simulation-warning");
    warningEl.style.display = "none";

    const baseSearch = document.getElementById("baseSearchAdCost").value;
    const baseLive = document.getElementById("baseLiveAdCost").value;
    const newSearch = document.getElementById("newSearchAdCost").value;
    const newLive = document.getElementById("newLiveAdCost").value;

    if (!baseSearch || !baseLive || !newSearch || !newLive) {
      warningEl.textContent = "모든 광고비 입력을 완료해주세요.";
      warningEl.style.display = "block";
      return;
    }

    const payload = {
      base_search_ad_cost: parseFloat(baseSearch) || 0,
      base_live_ad_cost: parseFloat(baseLive) || 0,
      base_competitor_event: document.getElementById("baseCompetitorEvent").value,
      new_search_ad_cost: parseFloat(newSearch) || 0,
      new_live_ad_cost: parseFloat(newLive) || 0,
      new_competitor_event: document.getElementById("newCompetitorEvent").value,
    };

    const res = await fetch("/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const r = await res.json();
    if (!r.success) return;

    document.getElementById("result-revenue").innerHTML = `<b style="color:#0077b6">${Number(r.new_revenue).toLocaleString()} 원</b>`;
    document.getElementById("result-revenue-change").innerHTML = `<b style="color:${r.revenue_change >= 0 ? "#2ec4b6" : "#ff9f1c"}">
      ${r.revenue_change >= 0 ? "+" : ""}${Number(r.revenue_change).toLocaleString()} 원</b>`;

    document.getElementById("result-roi").innerHTML = `<b style="color:#0f9d58">${Number(r.new_roi).toFixed(2)}</b>`;
    document.getElementById("result-roi-change").innerHTML = `<b style="color:${r.roi_change >= 0 ? "#2ec4b6" : "#ff9f1c"}">
      ${r.roi_change >= 0 ? "+" : ""}${Number(r.roi_change).toFixed(2)}</b>`;

    const nextIndex = simData.x.length + 1;

    if (simData.x.length === 0) {
      simData.x.push(0);
      simData.revenue.push(Number(r.base_revenue));
      simData.roi.push(Number(r.base_roi));
    }

    simData.x.push(nextIndex);
    simData.revenue.push(Number(r.new_revenue));
    simData.roi.push(Number(r.new_roi));

    Plotly.update("simChart", {
      x: [simData.x, simData.x],
      y: [simData.revenue, simData.roi],
    });
  } catch (e) {
    console.error("runSimulation() 오류:", e);
  }
}
