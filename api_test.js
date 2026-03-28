// =====================================
// GraphTools API Tester v3
// 永続化対応（localStorage）完全版
// =====================================

// -------------------------------------
// 永続化：localStorage から復元
// -------------------------------------
let results = [];
const STORAGE_KEY = "graphTools_test_results";

function loadResults() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      results = JSON.parse(saved);
    }
  } catch (e) {
    console.error("Failed to load results:", e);
  }
}

function saveResults() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(results));
  } catch (e) {
    console.error("Failed to save results:", e);
  }
}

loadResults();  // ← ページ読み込み時に復元

// -------------------------------------
// ログ表示
// -------------------------------------
function log(msg) {
  const panel = document.getElementById("log-panel");
  const t = new Date().toLocaleTimeString("ja-JP", { hour12: false });
  panel.textContent += `[${t}] ${msg}\n`;
  panel.scrollTop = panel.scrollHeight;
}

// -------------------------------------
// テスト実行
// -------------------------------------
async function runTest(type) {
  const base = document.getElementById("api-base").value;
  let url = "";
  let method = "GET";
  let body = null;

  // ---- API mapping ----
  const map = {
    init:               { url: "/init", method: "POST" },
    scatter_raw:        { url: "/scatter?mode=raw" },
    scatter_dense:      { url: "/scatter?mode=dense" },
    scatter_cluster:    { url: "/scatter?mode=cluster" },
    hierarchy_cluster:  { url: "/hierarchy?mode=cluster" },
    dump:               { url: "/dump" },
    health:             { url: "/health" },
    health_detail:      { url: "/health/detail" },
    queue:              { url: "/queue" },
    jobs:               { url: "/jobs" },
    latency:            { url: "/latency" },
    scatter_count:      { url: "/scatter/count" },
    hierarchy_structure:{ url: "/hierarchy/structure" },
    dump_consistency:   { url: "/dump/consistency" }
  };

  if (!map[type]) {
    log(`Unknown test: ${type}`);
    return;
  }

  url = base + map[type].url;
  method = map[type].method || "GET";
  body = map[type].body || null;

  log(`FETCH ${url}`);

  const start = performance.now();
  let result = {};
  let ok = false;

  try {
    const res = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : null
    });

    const text = await res.text();
    try {
      result = JSON.parse(text);
    } catch {
      result = { raw: text };
    }

    ok = res.ok;
  } catch (e) {
    result = { error: String(e) };
  }

  const duration = Math.floor(performance.now() - start);

  appendResult(type, ok, duration, result);
}

// -------------------------------------
// 結果追加（永続化）
// -------------------------------------
function appendResult(test, ok, duration, detail) {
  results.push({ test, ok, duration, detail });
  saveResults();   // ← 永続化
  renderResults(); // ← UI 再描画
}

// -------------------------------------
// UI 再描画
// -------------------------------------
function renderResults() {
  const tbody = document.getElementById("result-body");
  tbody.innerHTML = "";

  for (const r of results) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${r.test}</td>
      <td style="color:${r.ok ? 'green' : 'red'}">${r.ok ? 'OK' : 'FAIL'}</td>
      <td>${r.duration}</td>
      <td><pre style="white-space:pre-wrap;">${escapeHtml(JSON.stringify(r.detail, null, 2))}</pre></td>
    `;
    tbody.appendChild(tr);
  }

  tbody.scrollTop = tbody.scrollHeight;
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

// -------------------------------------
// JSON 保存（全履歴）
// -------------------------------------
function downloadJson() {
  if (results.length === 0) return alert("No results yet.");

  const blob = new Blob(
    [JSON.stringify(results, null, 2)],
    { type: "application/json" }
  );

  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `graphTools_test_all_${timestamp()}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

// -------------------------------------
// TEXT 保存（全履歴）
// -------------------------------------
function downloadText() {
  if (results.length === 0) return alert("No results yet.");

  const text = JSON.stringify(results, null, 2);
  const blob = new Blob([text], { type: "text/plain" });

  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `graphTools_test_all_${timestamp()}.txt`;
  a.click();
  URL.revokeObjectURL(url);
}

// -------------------------------------
function timestamp() {
  const d = new Date();
  return `${d.getFullYear()}${pad(d.getMonth()+1)}${pad(d.getDate())}_${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`;
}

function pad(n) {
  return n < 10 ? "0" + n : n;
}

// -------------------------------------
// 初回描画（永続化データ）
// -------------------------------------
window.addEventListener("DOMContentLoaded", renderResults);
