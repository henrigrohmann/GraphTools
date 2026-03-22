"use strict";

// ============================================================
// 基本設定
// ============================================================

const DEFAULT_BASE = "http://127.0.0.1:8005";

const state = {
  rows: [],
};

function $(id) {
  return document.getElementById(id);
}

function nowIso() {
  return new Date().toISOString();
}

// ============================================================
// API Base 自動検出（GraphTool 本体と完全統一）
// ============================================================

function detectApiBase() {
  const paramBase = new URLSearchParams(window.location.search).get("apiBase");
  if (paramBase) return paramBase.replace(/\/$/, "");

  const origin = window.location.origin;

  if (origin.includes(".app.github.dev")) {
    return origin.replace(/-\d+\.app\.github\.dev$/, "-8005.app.github.dev");
  }

  if (/localhost|127\.0\.0\.1/.test(origin)) {
    return origin.replace(/:\d+$/, ":8005");
  }

  return DEFAULT_BASE;
}

function getBase() {
  return $("apiBase").value.trim().replace(/\/$/, "");
}

// ============================================================
// ログ（GraphTool 本体と統一）
// ============================================================

function writeLog(message) {
  const panel = $("log");
  if (!panel) return;

  const time = new Date().toLocaleTimeString("ja-JP", { hour12: false });
  panel.textContent += `[${time}] ${message}\n`;
  panel.scrollTop = panel.scrollHeight;
}

function setStatus(message, ok = true) {
  const el = $("status");
  el.textContent = message;
  el.className = ok ? "ok" : "ng";
}

// ============================================================
// HTML エスケープ
// ============================================================

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

// ============================================================
// fetchJson / postJson（GraphTool 本体と統一）
// ============================================================

async function fetchJson(path) {
  const url = `${getBase()}${path}`;
  writeLog(`FETCH ${url}`);

  const res = await fetch(url);
  const text = await res.text();
  writeLog(`STATUS ${res.status} ${path}`);

  let json = {};
  if (text) {
    try {
      json = JSON.parse(text);
    } catch {
      throw new Error(`Invalid JSON from ${path}: ${text.slice(0, 160)}`);
    }
  }

  if (!res.ok) {
    const detail = json?.detail ? JSON.stringify(json.detail) : text.slice(0, 160);
    throw new Error(`HTTP ${res.status} ${path}: ${detail}`);
  }

  return json;
}

async function postJson(path, body = {}) {
  const url = `${getBase()}${path}`;
  writeLog(`POST ${url}`);

  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const text = await res.text();
  writeLog(`STATUS ${res.status} ${path}`);

  let json = {};
  if (text) {
    try {
      json = JSON.parse(text);
    } catch {
      throw new Error(`Invalid JSON from ${path}: ${text.slice(0, 160)}`);
    }
  }

  if (!res.ok) {
    const detail = json?.detail ? JSON.stringify(json.detail) : text.slice(0, 160);
    throw new Error(`HTTP ${res.status} ${path}: ${detail}`);
  }

  return json;
}

// ============================================================
// 結果テーブル
// ============================================================

function appendResult({ name, ok, durationMs, detail }) {
  state.rows.push({
    at: nowIso(),
    name,
    ok,
    durationMs,
    detail,
  });

  const tr = document.createElement("tr");
  tr.innerHTML = `
    <td>${name}</td>
    <td class="${ok ? "ok" : "ng"}">${ok ? "PASS" : "FAIL"}</td>
    <td>${durationMs}</td>
    <td>${escapeHtml(detail)}</td>
  `;
  $("resultBody").appendChild(tr);
}

function clearResults() {
  state.rows = [];
  $("resultBody").innerHTML = "";
  $("log").textContent = "";
  setStatus("結果をクリアしました", true);
}

// ============================================================
// 保存（GraphTool 本体と統一）
// ============================================================

function saveTextFile(filename, content, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function saveJson() {
  const payload = {
    timestamp_utc: nowIso(),
    api_base: getBase(),
    records: state.rows,
  };
  saveTextFile(
    `api_tester_${new Date().toISOString().replaceAll(":", "-")}.json`,
    JSON.stringify(payload, null, 2),
    "application/json"
  );
}

function saveTxt() {
  saveTextFile(
    `api_tester_${new Date().toISOString().replaceAll(":", "-")}.txt`,
    $("log").textContent,
    "text/plain"
  );
}

// ============================================================
// アサーション（新バックエンド仕様 v1.5）
// ============================================================

function assertInitPayload(payload) {
  if (typeof payload?.data !== "object" || payload.data === null) {
    throw new Error("init: data missing or invalid");
  }
  if (typeof payload?.cluster !== "object" || payload.cluster === null) {
    throw new Error("init: cluster missing or invalid");
  }
}

function assertScatterPayload(mode, payload) {
  if (!Array.isArray(payload)) {
    throw new Error(`scatter(${mode}): must be array`);
  }
  if (payload.length === 0) {
    throw new Error(`scatter(${mode}): empty array`);
  }
  const first = payload[0];
  if (typeof first.id !== "string") {
    throw new Error(`scatter(${mode}): item.id must be string`);
  }
  if (typeof first.x !== "number" || typeof first.y !== "number") {
    throw new Error(`scatter(${mode}): x/y must be number`);
  }
}

function assertHierarchyPayload(mode, payload) {
  if (typeof payload?.source !== "string") {
    throw new Error(`hierarchy(${mode}): source must be string`);
  }
  if (typeof payload?.raw !== "string") {
    throw new Error(`hierarchy(${mode}): raw must be string`);
  }
}

function assertDumpPayload(payload) {
  if (typeof payload?.tables !== "object" || payload.tables === null) {
    throw new Error("dump: tables missing or invalid");
  }
  if (!Array.isArray(payload?.recent_jobs)) {
    throw new Error("dump: recent_jobs must be array");
  }
}

// ============================================================
// テスト関数（正史 v1.5 — 新バックエンド対応）
// ============================================================

// Test 1: POST /init → GET /scatter?mode=raw
async function test1PipelineAndScatter() {
  const init = await postJson("/init");
  assertInitPayload(init);
  const scatter = await fetchJson("/scatter?mode=raw");
  assertScatterPayload("raw", scatter);
  return `init rows=${init.data?.rows ?? "?"} scatter count=${scatter.length}`;
}

// Test 2: GET /scatter?mode=cluster → GET /hierarchy?mode=cluster
async function test2ClusterAndHierarchy() {
  const scatter = await fetchJson("/scatter?mode=cluster");
  assertScatterPayload("cluster", scatter);
  const hierarchy = await fetchJson("/hierarchy?mode=cluster");
  assertHierarchyPayload("cluster", hierarchy);
  return `scatter count=${scatter.length} hierarchy source=${hierarchy.source}`;
}

// Test 3: GET /scatter?mode=dense → GET /hierarchy?mode=dense
async function test3DenseAndHierarchy() {
  const scatter = await fetchJson("/scatter?mode=dense");
  assertScatterPayload("dense", scatter);
  const hierarchy = await fetchJson("/hierarchy?mode=dense");
  assertHierarchyPayload("dense", hierarchy);
  return `scatter count=${scatter.length}`;
}

// Test 4: GET /dump
async function test4Jobs() {
  const dump = await fetchJson("/dump");
  assertDumpPayload(dump);
  return `jobs=${dump.recent_jobs.length} tables=${Object.keys(dump.tables).length}`;
}

// ============================================================
// テスト実行
// ============================================================

async function runTest(name, testFn) {
  const t0 = performance.now();
  writeLog(`START ${name}`);

  try {
    const detail = await testFn();
    const durationMs = Math.round(performance.now() - t0);
    appendResult({ name, ok: true, durationMs, detail });
    writeLog(`PASS ${name} (${durationMs}ms) ${detail}`);
  } catch (err) {
    const durationMs = Math.round(performance.now() - t0);
    const message = err instanceof Error ? err.message : String(err);
    appendResult({ name, ok: false, durationMs, detail: message });
    writeLog(`FAIL ${name} (${durationMs}ms) ${message}`);
  }
}

// ============================================================
// 接続確認
// ============================================================

async function runHealth() {
  const base = getBase();
  if (!base) {
    setStatus("API Base を入力してください", false);
    return;
  }

  try {
    const payload = await fetchJson("/health");
    setStatus(`接続OK: status=${payload.status} db=${payload.db_exists}`, true);
    writeLog(`Health OK: status=${payload.status}`);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    setStatus(`接続NG: ${message}`, false);
    writeLog(`Health NG: ${message}`);
  }
}

// ============================================================
// 全テスト
// ============================================================

async function runAll() {
  await runTest("Test 1: init/raw", test1PipelineAndScatter);
  await runTest("Test 2: cluster/hierarchy", test2ClusterAndHierarchy);
  await runTest("Test 3: dense/hierarchy", test3DenseAndHierarchy);
  await runTest("Test 4: dump", test4Jobs);
}

// ============================================================
// 初期化（イベント登録）
// ============================================================

document.addEventListener("DOMContentLoaded", () => {
  // API Base 初期値
  $("apiBase").value = detectApiBase();

  // 自動検出
  $("btnDetect").addEventListener("click", () => {
    $("apiBase").value = detectApiBase();
    setStatus(`API Base を自動設定: ${getBase()}`, true);
  });

  // 接続確認
  $("btnHealth").addEventListener("click", runHealth);

  // 個別テスト
  $("btnT1").addEventListener("click", () =>
    runTest("Test 1: init/raw", test1PipelineAndScatter)
  );
  $("btnT2").addEventListener("click", () =>
    runTest("Test 2: cluster/hierarchy", test2ClusterAndHierarchy)
  );
  $("btnT3").addEventListener("click", () =>
    runTest("Test 3: dense/hierarchy", test3DenseAndHierarchy)
  );
  $("btnT4").addEventListener("click", () =>
    runTest("Test 4: dump", test4Jobs)
  );

  // 全テスト
  $("btnAll").addEventListener("click", runAll);

  // 結果クリア
  $("btnClear").addEventListener("click", clearResults);

  // 保存
  $("btnSaveJson").addEventListener("click", saveJson);
  $("btnSaveTxt").addEventListener("click", saveTxt);

  setStatus("API tester initialized", true);
  writeLog("API tester initialized");
});
