// ===============================
//  API Base 自動検出
// ===============================
let API_BASE = "";

function detectApiBase() {
  const url = window.location.href;

  // Codespaces
  if (url.includes(".app.github.dev")) {
    const m = url.match(/https:\/\/(.+)-8002\.app\.github\.dev/);
    if (m) {
      API_BASE = `https://${m[1]}-8005.app.github.dev`;
    }
  }

  // ローカル
  if (!API_BASE) {
    API_BASE = "http://localhost:8005";
  }

  document.getElementById("api-base-text").textContent = API_BASE;
}

// ===============================
//  ログ出力
// ===============================
function logMessage(msg) {
  const panel = document.getElementById("log-panel");
  panel.textContent += msg + "\n";
  panel.scrollTop = panel.scrollHeight;
}

// ===============================
//  汎用 API 呼び出し
// ===============================
async function callApi(path) {
  const url = API_BASE + path;
  logMessage(`GET ${url}`);

  try {
    const res = await fetch(url);
    const data = await res.json();
    logMessage(JSON.stringify(data, null, 2));
  } catch (e) {
    logMessage("ERROR: " + e);
  }
}

// ===============================
//  初期化
// ===============================
window.addEventListener("DOMContentLoaded", () => {
  detectApiBase();
  logMessage("API Tester Ready.");
});
