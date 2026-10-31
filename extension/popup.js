const chat = document.getElementById("chat");
const input = document.getElementById("question");
const send = document.getElementById("send");

function clearEmptyState() {
  const empty = chat.querySelector(".empty-state");
  if (empty) empty.remove();
}

function timeToSeconds(t) {
  return t.split(":").reduce((total, part) => total * 60 + Number(part), 0);
}

function formatMarkdown(text, videoId) {
  let safe = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  safe = safe.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  safe = safe.replace(/\[(\d{1,2}(?::\d{2}){1,2})\]/g, (match, t) =>
    `<a href="https://youtu.be/${encodeURIComponent(videoId)}?t=${timeToSeconds(t)}" target="_blank" rel="noopener">${t}</a>`
  );

  const lines = safe.split("\n");
  let html = "";
  let inList = false;

  for (let line of lines) {
    const trimmed = line.trim();
    if (/^-\s+/.test(trimmed)) {
      if (!inList) { html += "<ul>"; inList = "ul"; }
      html += "<li>" + trimmed.replace(/^-\s+/, "") + "</li>";
    } else if (/^\d+\.\s+/.test(trimmed)) {
      if (!inList) { html += "<ol>"; inList = "ol"; }
      html += "<li>" + trimmed.replace(/^\d+\.\s+/, "") + "</li>";
    } else {
      if (inList) { html += inList === "ol" ? "</ol>" : "</ul>"; inList = false; }
      if (trimmed) html += "<p>" + trimmed + "</p>";
    }
  }
  if (inList) html += inList === "ol" ? "</ol>" : "</ul>";

  return html;
}

function addBubble(text, who, videoId) {
  clearEmptyState();
  const row = document.createElement("div");
  row.className = "row " + who;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = who === "user" ? "U" : "B";

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  if (who === "bot") {
    bubble.innerHTML = formatMarkdown(text, videoId);
  } else {
    bubble.textContent = text;
  }

  if (who === "user") {
    row.appendChild(bubble);
    row.appendChild(avatar);
  } else {
    row.appendChild(avatar);
    row.appendChild(bubble);
  }

  chat.appendChild(row);
  chat.scrollTop = chat.scrollHeight;
  return bubble;
}

function addTyping() {
  clearEmptyState();
  const row = document.createElement("div");
  row.className = "row bot";
  row.innerHTML = `<div class="avatar">B</div>
    <div class="bubble typing"><span></span><span></span><span></span></div>`;
  chat.appendChild(row);
  chat.scrollTop = chat.scrollHeight;
  return row;
}

function getVideoId(url) {
  const match = url.match(/[?&]v=([^&]+)/);
  return match ? match[1] : null;
}

async function ask() {
  const question = input.value.trim();
  if (!question) return;

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const videoId = getVideoId(tab.url);

  if (!videoId) {
    addBubble("Open a YouTube video first!", "bot");
    return;
  }

  addBubble(question, "user");
  input.value = "";
  send.disabled = true;

  const typingRow = addTyping();

  try {
    const res = await fetch("http://localhost:8000/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ video_id: videoId, question })
    });
    const data = await res.json();
    typingRow.remove();
    addBubble(data.answer, "bot", videoId);
  } catch (e) {
    typingRow.remove();
    addBubble("Could not reach the server. Is it running?", "bot");
  } finally {
    send.disabled = false;
  }
}

send.onclick = ask;
input.addEventListener("keydown", (e) => { if (e.key === "Enter") ask(); });