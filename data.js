// @ts-nocheck
console.log("data.js loaded");

// 現在の origin を取得
const origin = window.location.origin;

// ポート番号を抽出（なければ null）
const portMatch = origin.match(/:(\d+)/);
const currentPort = portMatch ? portMatch[1] : null;

// API のポートを決定
// ローカル開発 → 8001
// Codespaces → 8001（ポートフォワードされる）
const API_PORT = "8001";

// origin のポートだけ差し替える
let API_BASE;
if (currentPort) {
  // 例: http://localhost:5500 → http://localhost:8001
  API_BASE = origin.replace(`:${currentPort}`, `:${API_PORT}`);
} else {
  // 例: https://xxxxx-5500.app.github.dev → https://xxxxx-8001.app.github.dev
  API_BASE = origin.replace("-5500", `-${API_PORT}`);
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
