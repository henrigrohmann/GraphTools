const DEFAULT_API_PORT = "8005";

const state = {
  logs: [],
  results: [],
};

function now() {
  return new Date();
}

function isoNow() {
  return now().toISOString();
}

function logLine(message) {
  const line = `[${new Date().toLocaleTimeString()}] ${message}`;
  state.logs.push(line);
  const el = document.getElementById("log");
  el.textContent = state.logs.join("\n");
  el.scrollTop = el.scrollHeight;
}

function setStatus(text, isError = false) {
  const el = document.getElementById("status");
  el.textContent = text;
  el.style.color = isError ? "#b42318" : "#667788";
}

function resolveApiBase() {
  const params = new URLSearchParams(window.location.search);
  const fromQuery = params.get("apiBase");
  if (fromQuery) return fromQuery.replace(/\/$/, "");

  const origin = window.location.origin;
  if (!origin || origin === "null") {
    return `http://127.0.0.1:${DEFAULT_API_PORT}`;
  }

  if (origin.includes(".app.github.dev")) {
    return origin.replace(/-\d+\.app\.github\.dev$/, `-${DEFAULT_API_PORT}.app.github.dev`);
  }

  if (/:\d+$/.test(origin)) {
    return origin.replace(/:\d+$/, `:${DEFAULT_API_PORT}`);
  }

  return `${origin}:${DEFAULT_API_PORT}`;
}

function getApiBase() {
  return document.getElementById("apiBase").value.trim().replace(/\/$/, "");
}

function parseJsonSafe(text) {
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch (_e) {
    return null;
  }
}

async function fetchEndpoint(path) {
  const base = getApiBase();
  const url = `${base}${path}`;
  const start = performance.now();
  logLine(`GET ${url}`);

  let res;
  try {
    res = await fetch(url, { method: "GET", headers: { Accept: "application/json" } });
  } catch (err) {
    const msg = `NETWORK ERROR: ${err?.message || err}`;
    logLine(msg);
    return {
      ok: false,
      url,
      status: 0,
      ms: Math.round(performance.now() - start),
      bodyText: "",
      json: null,
      error: msg,
    };
  }

  const bodyText = await res.text();
  const json = parseJsonSafe(bodyText);
  const ms = Math.round(performance.now() - start);

  if (!res.ok) {
    logLine(`HTTP ${res.status} ${res.statusText}`);
    return {
      ok: false,
      url,
      status: res.status,
      ms,
      bodyText,
      json,
      error: `HTTP ${res.status} ${res.statusText}`,
    };
  }

  logLine(`OK ${res.status} (${ms}ms)`);
  return { ok: true, url, status: res.status, ms, bodyText, json, error: null };
}

function assertPipelinePayload(path, payload) {
  if (!payload || payload.status !== "ok" || !Number.isInteger(payload.count) || payload.count < 0) {
    throw new Error(`${path}: invalid payload ${JSON.stringify(payload)}`);
  }
}

function assertScatterPayload(mode, payload) {
  if (!payload || !Number.isInteger(payload.count) || !Array.isArray(payload.data)) {
    throw new Error(`/scatter?mode=${mode}: invalid payload ${JSON.stringify(payload)}`);
  }
  if (payload.count !== payload.data.length) {
    throw new Error(`/scatter?mode=${mode}: count mismatch ${payload.count} != ${payload.data.length}`);
  }
}

function assertHierarchyDumpPayload(mode, payload) {
  if (!payload || !Array.isArray(payload.clusterList) || !Array.isArray(payload.argumentList)) {
    throw new Error(`/hierarchy_dump?mode=${mode}: invalid payload ${JSON.stringify(payload)}`);
  }
}

async function callAndAssert(path, validator) {
  const res = await fetchEndpoint(path);
  if (!res.ok) {
    const detail = res.bodyText ? ` body=${res.bodyText.slice(0, 300)}` : "";
    throw new Error(`${path}: ${res.error}${detail}`);
  }
  validator(res.json);
  return res;
}

function addResultRow(name, ok, ms, detail) {
  state.results.push({ name, ok, ms, detail, at: isoNow() });
  const tbody = document.getElementById("resultBody");
  const tr = document.createElement("tr");
  tr.innerHTML = [
    `<td>${name}</td>`,
    `<td class="${ok ? "ok" : "ng"}">${ok ? "PASS" : "FAIL"}</td>`,
    `<td>${ms}</td>`,
    `<td>${detail}</td>`,
  ].join("");
  tbody.appendChild(tr);
}

async function runTest(name, sequence) {
  setStatus(`${name} 実行中...`);
  const started = performance.now();
  logLine(`=== ${name} START ===`);

  try {
    await sequence();
    const ms = Math.round(performance.now() - started);
    addResultRow(name, true, ms, "すべて成功");
    setStatus(`${name} 成功`);
    logLine(`=== ${name} PASS (${ms}ms) ===`);
  } catch (err) {
    const ms = Math.round(performance.now() - started);
    const detail = String(err?.message || err);
    addResultRow(name, false, ms, detail.replace(/</g, "&lt;"));
    setStatus(`${name} 失敗`, true);
    logLine(`=== ${name} FAIL (${ms}ms) ===`);
    logLine(detail);
    throw err;
  }
}

async function runTest1() {
  await runTest("Test1: /raw -> /hierarchy_dump?mode=external", async () => {
    await callAndAssert("/raw", (p) => assertPipelinePayload("/raw", p));
    await callAndAssert("/hierarchy_dump?mode=external", (p) => assertHierarchyDumpPayload("external", p));
  });
}

async function runTest2() {
  await runTest("Test2: /cluster -> /hierarchy_dump?mode=cluster", async () => {
    await callAndAssert("/cluster", (p) => assertPipelinePayload("/cluster", p));
    await callAndAssert("/hierarchy_dump?mode=cluster", (p) => assertHierarchyDumpPayload("cluster", p));
  });
}

async function runTest3() {
  await runTest("Test3: /dense -> /hierarchy_dump?mode=dense", async () => {
    await callAndAssert("/dense", (p) => assertPipelinePayload("/dense", p));
    await callAndAssert("/hierarchy_dump?mode=dense", (p) => assertHierarchyDumpPayload("dense", p));
  });
}

async function runTest4() {
  await runTest("Test4: side-effect check raw/cluster/dense", async () => {
    await callAndAssert("/raw", (p) => assertPipelinePayload("/raw", p));
    await callAndAssert("/scatter?mode=raw", (p) => assertScatterPayload("raw", p));

    await callAndAssert("/cluster", (p) => assertPipelinePayload("/cluster", p));
    await callAndAssert("/scatter?mode=cluster", (p) => assertScatterPayload("cluster", p));

    await callAndAssert("/dense", (p) => assertPipelinePayload("/dense", p));
    await callAndAssert("/scatter?mode=dense", (p) => assertScatterPayload("dense", p));
  });
}

async function runAll() {
  setStatus("Run All 実行中...");
  try {
    await runTest1();
    await runTest2();
    await runTest3();
    await runTest4();
    setStatus("Run All 完了: すべて成功");
  } catch (_err) {
    setStatus("Run All 中断: 失敗あり", true);
  }
}

function clearResults() {
  state.results = [];
  state.logs = [];
  document.getElementById("resultBody").innerHTML = "";
  document.getElementById("log").textContent = "";
  setStatus("クリアしました");
}

function downloadTextFile(filename, text, mime) {
  const blob = new Blob([text], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function saveJson() {
  const payload = {
    generated_at: isoNow(),
    api_base: getApiBase(),
    results: state.results,
    logs: state.logs,
  };
  const stamp = isoNow().replace(/[:.]/g, "-");
  downloadTextFile(`api_test_log_${stamp}.json`, JSON.stringify(payload, null, 2), "application/json");
}

function saveTxt() {
  const stamp = isoNow().replace(/[:.]/g, "-");
  const lines = [];
  lines.push(`generated_at=${isoNow()}`);
  lines.push(`api_base=${getApiBase()}`);
  lines.push("");
  lines.push("[results]");
  for (const r of state.results) {
    lines.push(`${r.at} | ${r.name} | ${r.ok ? "PASS" : "FAIL"} | ${r.ms}ms | ${r.detail}`);
  }
  lines.push("");
  lines.push("[logs]");
  lines.push(...state.logs);
  downloadTextFile(`api_test_log_${stamp}.txt`, lines.join("\n"), "text/plain");
}

async function runHealth() {
  setStatus("接続確認中...");
  const res = await fetchEndpoint("/jobs");
  if (res.ok) {
    const count = Number.isInteger(res.json?.count) ? res.json.count : "?";
    setStatus(`接続OK (/jobs count=${count})`);
  } else {
    setStatus(`接続NG: ${res.error}`, true);
  }
}

function bindEvents() {
  document.getElementById("btnDetect").addEventListener("click", () => {
    document.getElementById("apiBase").value = resolveApiBase();
    setStatus("API Baseを自動検出しました");
  });

  document.getElementById("btnHealth").addEventListener("click", runHealth);
  document.getElementById("btnT1").addEventListener("click", () => runTest1().catch(() => {}));
  document.getElementById("btnT2").addEventListener("click", () => runTest2().catch(() => {}));
  document.getElementById("btnT3").addEventListener("click", () => runTest3().catch(() => {}));
  document.getElementById("btnT4").addEventListener("click", () => runTest4().catch(() => {}));
  document.getElementById("btnAll").addEventListener("click", runAll);
  document.getElementById("btnClear").addEventListener("click", clearResults);
  document.getElementById("btnSaveJson").addEventListener("click", saveJson);
  document.getElementById("btnSaveTxt").addEventListener("click", saveTxt);
}

window.addEventListener("DOMContentLoaded", () => {
  document.getElementById("apiBase").value = resolveApiBase();
  bindEvents();
  setStatus("準備完了");
  logLine(`apiBase=${getApiBase()}`);
});
