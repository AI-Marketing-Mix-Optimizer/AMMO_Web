const toggleBtn = document.getElementById('chatbot-toggle');
const chatWindow = document.getElementById('chatbot-window');
const chatBody = document.getElementById('chatbot-body');
const chatSend = document.getElementById('chatbot-send');
const chatInput = document.getElementById('chatbot-text');

toggleBtn.addEventListener('click', () => {
  chatWindow.style.display = chatWindow.style.display === 'flex' ? 'none' : 'flex';
  chatWindow.style.flexDirection = 'column';
});

chatSend.addEventListener('click', sendMessage);
chatInput.addEventListener('keypress', e => { if (e.key === 'Enter') sendMessage(); });

async function sendMessage() {
  const msg = chatInput.value.trim();
  if (!msg) return;

  appendMessage('user', msg);
  chatInput.value = '';
  appendMessage('bot', '분석 중...');

  const res = await fetch('/chatbot', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: msg })
  });
  const data = await res.json();

  if (data.success) {
    chatBody.lastChild.textContent =
      `${data.summary}\n\nROI: ${data.result.new_roi} / 매출 변화: ${data.result.revenue_change.toLocaleString()}원`;
    runSimulation(); // 그래프 자동 갱신
  } else {
    chatBody.lastChild.textContent = `오류: ${data.message}`;
  }
}

function appendMessage(sender, text) {
  const msg = document.createElement('div');
  msg.classList.add('chatbot-message', `chatbot-${sender}`);
  msg.textContent = text;
  chatBody.appendChild(msg);
  chatBody.scrollTop = chatBody.scrollHeight;
}
