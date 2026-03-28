// =====================================
// GraphTools API Tester v2
// 正史仕様復元版
// =====================================

let lastResult = null;   // ★ダウンロード用に保持

function log(msg) {
  const panel = document.getElementById("log-panel");
  const t = new Date().toLocaleTimeString("ja-JP", { hour12: false });
  panel.textContent += `[${t}] ${msg}\n`;
  panel.scrollTop = panel.scrollHeight;
}

async function runTest(type) {
  const base = document.getElementById("api-base").value;
  let url = "";
  let method = "GET";
  let body = null;

  if (type === "init") {
    url = `${base}/init`;
    method = "POST";
    body = {};
  } else if (type === "scatter_raw") {
    url = `${base}/scatter?mode=raw`;
  } else if (type === "scatter_dense") {
    url = `${base}/scatter?mode=dense`;
  } else if (type === "scatter_cluster") {
    url = `${base}/scatter?mode=cluster`;
  } else if (type === "hierarchy_cluster") {
    url = `${base}/hierarchy?mode=cluster`;
  } else if (type === "dump") {
    url = `${base}/dump`;
  } else if (type === "health") {
    url = `${base}/health`;
  }

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

  // ★テーブルに追加
  appendResult(type, ok, duration, result);

  // ★ダウンロード用に保持
  lastResult = result;
}

function appendResult(test, ok, duration, detail) {
  const tbody = document.getElementById("result-body");
  const tr = document.createElement("tr");

  tr.innerHTML = `
    <td>${test}</td>
    <td style="color:${ok ? 'green' : 'red'}">${ok ? 'OK' : 'FAIL'}</td>
    <td>${duration}</td>
    <td><pre style="white-space:pre-wrap;">${escapeHtml(JSON.stringify(detail, null, 2))}</pre></td>
  `;

  tbody.appendChild(tr);
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

// =====================================
// ★正史仕様：ダウンロード機能復元
// =====================================

function downloadJson() {
  if (!lastResult) return alert("No result yet.");

  const blob = new Blob(
    [JSON.stringify(lastResult, null, 2)],
    { type: "application/json" }
  );

  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `graphTools_test_${timestamp()}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

function downloadText() {
  if (!lastResult) return alert("No result yet.");

  const text = JSON.stringify(lastResult, null, 2);
  const blob = new Blob([text], { type: "text/plain" });

  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `graphTools_test_${timestamp()}.txt`;
  a.click();
  URL.revokeObjectURL(url);
}

function timestamp() {
  const d = new Date();
  return `${d.getFullYear()}${pad(d.getMonth()+1)}${pad(d.getDate())}_${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`;
}

function pad(n) {
  return n < 10 ? "0" + n : n;
}
