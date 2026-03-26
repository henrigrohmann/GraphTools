// ===== 設定 =====
let apiBase = "";

// テスト定義（ここに行を足せばエンドポイントが増やせる）
const apiTests = [
  { name: "Init", endpoint: "/init", method: "GET" },
  { name: "Scatter (raw)", endpoint: "/scatter?mode=raw", method: "GET" },
  { name: "Scatter (cluster)", endpoint: "/scatter?mode=cluster", method: "GET" },
  { name: "Scatter (dense)", endpoint: "/scatter?mode=dense", method: "GET" },
  { name: "Hierarchy (cluster)", endpoint: "/hierarchy?mode=cluster", method: "GET" },
  { name: "Dump", endpoint: "/dump", method: "GET" },
  { name: "Health", endpoint: "/health", method: "GET" }
];

// 結果の内部保持（保存用）
const resultRecords = [];

// ===== 初期化 =====
window.onload = () => {
  const apiBaseInput = document.getElementById("api-base");
  apiBase = apiBaseInput.value.trim();

  apiBaseInput.addEventListener("change", () => {
    apiBase = apiBaseInput.value.trim();
  });

  document.getElementById("btn-ping").onclick = pingServer;
  document.getElementById("btn-run-all").onclick = runAllTests;
  document.getElementById("btn-clear-results").onclick = clearResults;
  document.getElementById("btn-save-json").onclick = saveResultsAsJson;
  document.getElementById("btn-save-txt").onclick = saveResultsAsTxt;

  renderButtons();
  writeLog("Tester initialized.");
};

// ===== UI 描画 =====
function renderButtons() {
  const container = document.getElementById("test-buttons");
  container.innerHTML = "";

  apiTests.forEach(test => {
    const btn = document.createElement("button");
    btn.textContent = test.name;
    btn.className = "test-button";
    btn.onclick = () => runApiTest(test);
    container.appendChild(btn);
  });
}

// ===== ログ =====
function writeLog(message) {
  const log = document.getElementById("log");
  const now = new Date();
  const ts = now.toTimeString().split(" ")[0];
  log.textContent += `[${ts}] ${message}\n`;
  log.scrollTop = log.scrollHeight;
}

// ===== 接続確認 =====
async function pingServer() {
  const statusEl = document.getElementById("ping-status");
  statusEl.textContent = "接続確認中…";
  statusEl.style.color = "#333";

  const url = apiBase + "/health";
  writeLog(`PING ${url}`);

  try {
    const res = await fetch(url);
    if (res.ok) {
      statusEl.textContent = "接続OK";
      statusEl.style.color = "#0a0";
      writeLog("PING OK");
    } else {
      statusEl.textContent = `接続NG (${res.status})`;
      statusEl.style.color = "#c00";
      writeLog(`PING FAIL status=${res.status}`);
    }
  } catch (e) {
    statusEl.textContent = "接続エラー";
    statusEl.style.color = "#c00";
    writeLog(`PING ERROR: ${e}`);
  }
}

// ===== 単体テスト実行 =====
async function runApiTest(test) {
  const url = apiBase + test.endpoint;
  writeLog(`FETCH ${url}`);

  const start = performance.now();
  let ok = false;
  let detail = "";

  try {
    const res = await fetch(url, { method: test.method });
    let json = null;
    try {
      json = await res.json();
    } catch {
      // JSON でない場合もあるので、そのままテキストを読む
      const text = await res.text();
      json = { raw: text };
    }
    ok = res.ok;
    detail = JSON.stringify(json, null, 2).slice(0, 1000);
  } catch (e) {
    detail = e.toString();
  }

  const duration = performance.now() - start;
  addResult(test.name, ok, duration, detail);
}

// ===== 全テスト実行 =====
async function runAllTests() {
  writeLog("Run All Tests");
  for (const test of apiTests) {
    // 直列で順番に叩く（企業ネットワークでも安全）
    // 並列にしたい場合は Promise.all に変更可能
    // eslint-disable-next-line no-await-in-loop
    await runApiTest(test);
  }
}

// ===== 結果追加 =====
function addResult(name, ok, duration, detail) {
  const tbody = document.getElementById("result-body");
  const tr = document.createElement("tr");

  tr.innerHTML = `
    <td>${name}</td>
    <td style="color:${ok ? '#0a0' : '#c00'}; font-weight:bold;">
      ${ok ? "OK" : "FAIL"}
    </td>
    <td>${Math.round(duration)}</td>
    <td><pre style="white-space:pre-wrap; margin:0;">${escapeHtml(detail)}</pre></td>
  `;

  tbody.appendChild(tr);

  resultRecords.push({
    at: new Date().toISOString(),
    name,
    ok,
    durationMs: Math.round(duration),
    detail
  });
}

// ===== 結果クリア =====
function clearResults() {
  const tbody = document.getElementById("result-body");
  tbody.innerHTML = "";
  resultRecords.length = 0;
  writeLog("Results cleared.");
}

// ===== 結果保存（JSON） =====
function saveResultsAsJson() {
  if (resultRecords.length === 0) {
    writeLog("No results to save (JSON).");
    return;
  }
  const payload = {
    timestamp_utc: new Date().toISOString(),
    api_base: apiBase,
    records: resultRecords
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], {
    type: "application/json"
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "api_test_results.json";
  a.click();
  URL.revokeObjectURL(url);
  writeLog("Results saved as JSON.");
}

// ===== 結果保存（TXT） =====
function saveResultsAsTxt() {
  if (resultRecords.length === 0) {
    writeLog("No results to save (TXT).");
    return;
  }
  let lines = [];
  lines.push(`timestamp_utc: ${new Date().toISOString()}`);
  lines.push(`api_base: ${apiBase}`);
  lines.push("");
  for (const r of resultRecords) {
    lines.push(`[${r.at}] ${r.name} ${r.ok ? "OK" : "FAIL"} (${r.durationMs}ms)`);
    lines.push(r.detail);
    lines.push("");
  }
  const blob = new Blob([lines.join("\n")], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "api_test_results.txt";
  a.click();
  URL.revokeObjectURL(url);
  writeLog("Results saved as TXT.");
}

// ===== HTML エスケープ =====
function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}
