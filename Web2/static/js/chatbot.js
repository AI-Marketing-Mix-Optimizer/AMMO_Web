// 챗봇 열기/닫기
document.getElementById("chatbot-toggle").onclick = () => {
    document.getElementById("chatbot-window").style.display = "flex";
};

document.getElementById("chatbot-close").onclick = () => {
    document.getElementById("chatbot-window").style.display = "none";
};

// 메시지 렌더링 함수
function addMessage(text, sender = "bot") {
    const msg = document.createElement("div");
    msg.classList.add("chat-message");
    msg.classList.add(sender === "user" ? "user-msg" : "bot-msg");

    if (sender === "bot") {
        msg.innerHTML = text;   // HTML 렌더링
    } else {
        msg.innerText = text;   // user 입력 텍스트 처리
    }

    document.getElementById("chat-body").appendChild(msg);

    const body = document.getElementById("chat-body");
    body.scrollTop = body.scrollHeight;
}

// 메시지 전송
document.getElementById("chat-send").onclick = async () => {
    const input = document.getElementById("chat-input");
    const question = input.value.trim();
    if (!question) return;

    addMessage(question, "user");
    input.value = "";

    // 서버로 질문 보내기
    const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: question })
    });

    const data = await res.json();
    addMessage(data.reply, "bot");
};
document.querySelectorAll('.suggest').forEach(btn => {
    btn.addEventListener('click', () => {
        const q = btn.innerText;

        // 사용자 말풍선 추가
        addMessage(q, "user");

        // 서버로 질문 보내기
        fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: q })
        })
            .then(res => res.json())
            .then(data => addMessage(data.reply, "bot"));
    });
});


// chat_simulate.html 시뮬레이터 값 채우기 + LLM 설명 채우기
async function viewSimulation({
    baseRevenue,
    newRevenue,
    baseRoi,
    newRoi,
    revenueChange,
    roiChange,
    base_search_ad_cost,
    base_live_ad_cost,
    new_search_ad_cost,
    new_live_ad_cost,
    promo_flag
}) {

    // ----- 화면 숫자 표시 -----
    document.getElementById("result-revenue").innerHTML =
        `<b style="color:#0077b6">${newRevenue.toLocaleString()} 원</b>`;

    document.getElementById("result-revenue-change").innerHTML =
        `<b style="color:${revenueChange >= 0 ? '#2ec4b6' : '#ff9f1c'}">
            ${revenueChange >= 0 ? '+' : ''}${revenueChange.toLocaleString()} 원
        </b>`;

    document.getElementById("result-roi").innerHTML =
        `<b style="color:#0f9d58">${newRoi.toFixed(2)}</b>`;

    document.getElementById("result-roi-change").innerHTML =
        `<b style="color:${roiChange >= 0 ? '#2ec4b6' : '#ff9f1c'}">
            ${roiChange >= 0 ? '+' : ''}${roiChange.toFixed(2)}
        </b>`;

    // ----- 그래프 -----
    const simData = {
        x: [0, 1],
        revenue: [baseRevenue, newRevenue],
        roi: [baseRoi, newRoi]
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
            yaxis: 'y1'
        },
        {
            x: simData.x,
            y: simData.roi,
            name: '예상 ROI',
            type: 'scatter',
            mode: 'lines+markers',
            line: { color: '#0f9d58', width: 3 },
            marker: { size: 8 },
            yaxis: 'y2'
        }
    ], {
        margin: { t: 20, l: 60, r: 60, b: 40 },
        xaxis: { title: '단계' },
        yaxis: { title: '매출액' },
        yaxis2: { title: 'ROI', overlaying: 'y', side: 'right' }
    });

    // ----- 해석 텍스트 영역 -----
    const textarea = document.getElementById("result_analysis");
    textarea.value = "LLM이 결과를 분석하는 중입니다...";
    textarea.classList.add("loading");

    // ----- 세션 캐시 Key 구성 -----
    const cacheKey =
        `analysis_${base_search_ad_cost}_${base_live_ad_cost}_${new_search_ad_cost}_${new_live_ad_cost}_${promo_flag}`;

    // ====== 1) 세션 스토리지에 캐시가 있으면 그대로 표시 ======
    const cached = sessionStorage.getItem(cacheKey);

    if (cached) {
        console.log("세션 캐시 적용 — interpret API 호출 스킵");
        textarea.classList.remove("loading");
        textarea.value = cached;
        return;   // API 호출 중단
    }

    // ====== 2) 캐시 없으면 interpret API 호출 ======
    const res = await fetch("/interpret", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            base_revenue: baseRevenue,
            new_revenue: newRevenue,
            base_roi: baseRoi,
            new_roi: newRoi,
            revenue_change: revenueChange,
            roi_change: roiChange,
            base_search_ad_cost,
            base_live_ad_cost,
            new_search_ad_cost,
            new_live_ad_cost,
            promo_flag
        })
    });

    const data = await res.json();
    textarea.classList.remove("loading");

    if (data.success) {
        textarea.value = data.analysis;

        // ====== 세션 캐시에 저장 ======
        sessionStorage.setItem(cacheKey, data.analysis);

    } else {
        textarea.value = "해석 실패: " + data.message;
    }
}
