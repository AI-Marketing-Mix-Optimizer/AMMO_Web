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
    msg.innerText = text;
    document.getElementById("chat-body").appendChild(msg);

    // 자동 스크롤
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
        headers: {"Content-Type": "application/json"},
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
