const chatbotWin = document.getElementById("chatbot-window");
const toggleBtn = document.getElementById("chatbot-toggle");

toggleBtn.onclick = () => {
    chatbotWin.style.display =
        chatbotWin.style.display === "flex" ? "none" : "flex";
};

document.getElementById("chatbot-close").onclick = () => {
    chatbotWin.style.display = "none";
};

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

function addMessage(text, sender = "bot") {
    const msg = document.createElement("div");
    msg.classList.add("chat-message");
    msg.classList.add(sender === "user" ? "user-msg" : "bot-msg");
    msg.innerHTML = sender === "bot" ? text : text;
    document.getElementById("chat-body").appendChild(msg);
    const body = document.getElementById("chat-body");
    body.scrollTop = body.scrollHeight;
}

document.getElementById("chat-send").onclick = async () => {
    const input = document.getElementById("chat-input");
    const question = input.value.trim();
    if (!question) return;

    addMessage(question, "user");
    input.value = "";
    showTyping();

    const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: question })
    });

    hideTyping();
    const data = await res.json();
    addMessage(data.reply, "bot");
};

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
    ]);

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
