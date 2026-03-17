// @ts-nocheck
console.log("data.js loaded");

// 現在の origin を取得
const origin = window.location.origin;

// Codespaces の場合は host に ".app.github.dev" が含まれる
const isCodespaces = origin.includes(".app.github.dev");

// API ポート
const API_PORT = "8001";

let API_BASE;

if (isCodespaces) {
  // 例: https://xxxxx-5500.app.github.dev → https://xxxxx-8001.app.github.dev
  API_BASE = origin.replace(/-\d+\.app\.github\.dev/, `-${API_PORT}.app.github.dev`);
} else {
  // ローカル: http://localhost:5500 → http://localhost:8001
  const portMatch = origin.match(/:(\d+)/);
  const currentPort = portMatch ? portMatch[1] : null;

  if (currentPort) {
    API_BASE = origin.replace(`:${currentPort}`, `:${API_PORT}`);
  } else {
    // ポートが無い環境（静的ホスティングなど）
    API_BASE = origin;
  }
}

console.log("API_BASE =", API_BASE);

window.api = {
  async getScatterData() {
    const url = `${API_BASE}/scatter_data`;
    console.log("FETCH:", url);

    const res = await fetch(url);
    console.log("STATUS:", res.status);

    const json = await res.json();
    console.log("JSON:", json);
    return json;
  }
};
