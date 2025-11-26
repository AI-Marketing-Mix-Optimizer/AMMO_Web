// 챗봇 열기/닫기
document.getElementById("chatbot-toggle").onclick = () => {
    document.getElementById("chatbot-window").style.display = "flex";
};

document.getElementById("chatbot-close").onclick = () => {
    document.getElementById("chatbot-window").style.display = "none";
};

// ============================
// 챗봇 타이핑 애니메이션
// ============================
let typingBubble = null;

function showTyping() {
    const body = document.getElementById("chat-body");
    typingBubble = document.createElement("div");
    typingBubble.classList.add("chat-message", "bot-typing");

    typingBubble.innerHTML = `
        <div class="dot"></div>
        <div class="dot"></div>
        <div class="dot"></div>
    `;

    body.appendChild(typingBubble);
    body.scrollTop = body.scrollHeight;
}

function hideTyping() {
    if (typingBubble) {
        typingBubble.remove();
        typingBubble = null;
    }
}

// ============================
// 메시지 렌더링 함수
// ============================
function addMessage(text, sender = "bot") {
    const msg = document.createElement("div");
    msg.classList.add("chat-message");
    msg.classList.add(sender === "user" ? "user-msg" : "bot-msg");

    if (sender === "bot") {
        msg.innerHTML = text;   
    } else {
        msg.innerText = text;   
    }

    document.getElementById("chat-body").appendChild(msg);

    const body = document.getElementById("chat-body");
    body.scrollTop = body.scrollHeight;
}

// ============================
// 메시지 전송
// ============================
document.getElementById("chat-send").onclick = async () => {
    const input = document.getElementById("chat-input");
    const question = input.value.trim();

    if (!question) return;

    // 사용자 메시지 표시
    addMessage(question, "user");
    input.value = "";

    // 타이핑 표시
    showTyping();

    // 서버로 전송
    const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: question })
    });

    // 타이핑 제거
    hideTyping();

    const data = await res.json();

    // 챗봇 메시지 표시
    addMessage(data.reply, "bot");
};

// ============================
// 추천 질문(suggest)
// ============================
document.querySelectorAll(".suggest").forEach(btn => {
    btn.addEventListener("click", () => {
        const q = btn.innerText;

        addMessage(q, "user");

        showTyping();

        fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: q })
        })
        .then(res => res.json())
        .then(data => {
            hideTyping();
            addMessage(data.reply, "bot");
        });
    });
});

// ============================
// chat_simulate.html 연동
// ============================
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
    base_promo_flag,
    new_promo_flag
}) {
    document.getElementById("result-revenue").innerHTML =
        `<b style="color:#0077b6">${Math.round(newRevenue).toLocaleString()} 원</b>`;

    document.getElementById("result-revenue-change").innerHTML =
        `<b style="color:${revenueChange >= 0 ? '#2ec4b6' : '#ff9f1c'}">
            ${revenueChange >= 0 ? '+' : ''}${Math.round(revenueChange).toLocaleString()} 원
        </b>`;

    document.getElementById("result-roi").innerHTML =
        `<b style="color:#0f9d58">${newRoi.toFixed(2)}</b>`;

    document.getElementById("result-roi-change").innerHTML =
        `<b style="color:${roiChange >= 0 ? '#2ec4b6' : '#ff9f1c'}">
            ${roiChange >= 0 ? '+' : ''}${roiChange.toFixed(2)}
        </b>`;

    const simData = {
        x: [0, 1],
        revenue: [baseRevenue, newRevenue],
        roi: [baseRoi, newRoi]
    };

    Plotly.newPlot("simChart", [
        {
            x: simData.x,
            y: simData.revenue,
            name: "예상 매출액",
            type: "scatter",
            mode: "lines+markers",
            line: { color: "#0077b6", width: 3 },
            marker: { size: 8 },
            yaxis: "y1"
        },
        {
            x: simData.x,
            y: simData.roi,
            name: "예상 ROI",
            type: "scatter",
            mode: "lines+markers",
            line: { color: "#0f9d58", width: 3 },
            marker: { size: 8 },
            yaxis: "y2"
        }
    ], {
        margin: { t: 20, l: 60, r: 60, b: 40 },
        xaxis: { title: "단계" },
        yaxis: { title: "매출액" },
        yaxis2: { title: "ROI", overlaying: "y", side: "right" }
    });

    const textarea = document.getElementById("result_analysis");
    textarea.value = "LLM이 결과를 분석하는 중입니다...";
    textarea.classList.add("loading");

    const cacheKey =
        `analysis_${base_search_ad_cost}_${base_live_ad_cost}_${new_search_ad_cost}_${new_live_ad_cost}_${base_promo_flag}_${new_promo_flag}`;

    const cached = sessionStorage.getItem(cacheKey);

    if (cached) {
        textarea.classList.remove("loading");
        textarea.value = cached;
        return;
    }

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
            base_promo_flag,
            new_promo_flag
        })
    });

    const data = await res.json();
    textarea.classList.remove("loading");

    if (data.success) {
        textarea.value = data.analysis;
        sessionStorage.setItem(cacheKey, data.analysis);
    } else {
        textarea.value = "해석 실패: " + data.message;
    }
}
