"use strict";

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

function writeLog(line) {
  const el = $("log");
  const stamp = new Date().toLocaleTimeString("ja-JP", { hour12: false });
  el.textContent += `[${stamp}] ${line}\n`;
  el.scrollTop = el.scrollHeight;
}

function setStatus(message, ok = true) {
  const el = $("status");
  el.textContent = message;
  el.className = ok ? "ok" : "ng";
}

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

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

async function fetchJson(path) {
  const url = `${getBase()}${path}`;
  const res = await fetch(url);
  const text = await res.text();

  let json;
  try {
    json = text ? JSON.parse(text) : {};
  } catch {
    throw new Error(`Invalid JSON from ${path}: ${text.slice(0, 160)}`);
  }

  if (!res.ok) {
    const detail = json?.detail ? JSON.stringify(json.detail) : text.slice(0, 160);
    throw new Error(`HTTP ${res.status} ${path}: ${detail}`);
  }

  return json;
}

function assertPipelinePayload(name, payload) {
  if (payload?.status !== "ok") {
    throw new Error(`${name}: status must be ok`);
  }
  if (!Number.isInteger(payload?.count) || payload.count < 0) {
    throw new Error(`${name}: invalid count`);
  }
}

function assertScatterPayload(mode, payload) {
  if (!Number.isInteger(payload?.count) || payload.count < 0) {
    throw new Error(`scatter(${mode}): invalid count`);
  }
  if (!Array.isArray(payload?.data)) {
    throw new Error(`scatter(${mode}): data must be an array`);
  }
  if (payload.count !== payload.data.length) {
    throw new Error(`scatter(${mode}): count mismatch`);
  }
}

function assertJobsPayload(payload) {
  if (!Number.isInteger(payload?.count) || payload.count < 0) {
    throw new Error("jobs: invalid count");
  }
  if (!Array.isArray(payload?.jobs)) {
    throw new Error("jobs: jobs must be an array");
  }
  if (payload.count !== payload.jobs.length) {
    throw new Error("jobs: count mismatch");
  }
}

// New hierarchy shape: clusterList[].memberIds + argumentList[]
// Legacy shape: argumentList with children references
function assertHierarchyPayload(mode, payload) {
  if (!Array.isArray(payload?.clusterList)) {
    throw new Error(`hierarchy(${mode}): clusterList must be an array`);
  }
  if (!Array.isArray(payload?.argumentList)) {
    throw new Error(`hierarchy(${mode}): argumentList must be an array`);
  }

  const argMap = new Map();
  for (const arg of payload.argumentList) {
    if (!arg || typeof arg.id !== "string") {
      throw new Error(`hierarchy(${mode}): argument id missing`);
    }
    argMap.set(arg.id, arg);
  }

  for (const cluster of payload.clusterList) {
    if (!cluster || typeof cluster.id !== "string") {
      throw new Error(`hierarchy(${mode}): cluster id missing`);
    }

    if (Array.isArray(cluster.memberIds)) {
      for (const memberId of cluster.memberIds) {
        if (!argMap.has(memberId)) {
          throw new Error(`hierarchy(${mode}): missing argument for memberId=${memberId}`);
        }
      }
    }
  }
}

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

async function test1PipelineAndScatter() {
  const raw = await fetchJson("/raw");
  assertPipelinePayload("/raw", raw);

  const scatter = await fetchJson("/scatter?mode=raw");
  assertScatterPayload("raw", scatter);

  return `raw count=${raw.count}, scatter count=${scatter.count}`;
}

async function test2ClusterAndHierarchy() {
  const cluster = await fetchJson("/cluster");
  assertPipelinePayload("/cluster", cluster);

  const scatter = await fetchJson("/scatter?mode=cluster");
  assertScatterPayload("cluster", scatter);

  const hierarchy = await fetchJson("/hierarchy?mode=cluster");
  assertHierarchyPayload("cluster", hierarchy);

  return `cluster count=${cluster.count}, hierarchy clusters=${hierarchy.clusterList.length}`;
}

async function test3DenseAndHierarchy() {
  const dense = await fetchJson("/dense");
  assertPipelinePayload("/dense", dense);

  const scatter = await fetchJson("/scatter?mode=dense");
  assertScatterPayload("dense", scatter);

  const hierarchy = await fetchJson("/hierarchy?mode=dense");
  assertHierarchyPayload("dense", hierarchy);

  return `dense count=${dense.count}, hierarchy clusters=${hierarchy.clusterList.length}`;
}

async function test4Jobs() {
  const jobs = await fetchJson("/jobs");
  assertJobsPayload(jobs);
  return `jobs count=${jobs.count}`;
}

async function runHealth() {
  const base = getBase();
  if (!base) {
    setStatus("API Base を入力してください", false);
    return;
  }

  try {
    const healthUrl = `${base}/docs`;
    const res = await fetch(healthUrl, { method: "GET" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    setStatus(`接続OK: ${healthUrl}`, true);
    writeLog(`Health OK: ${healthUrl}`);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    setStatus(`接続NG: ${message}`, false);
    writeLog(`Health NG: ${message}`);
  }
}

async function runAll() {
  await runTest("Test 1: raw/scatter", test1PipelineAndScatter);
  await runTest("Test 2: cluster/hierarchy", test2ClusterAndHierarchy);
  await runTest("Test 3: dense/hierarchy", test3DenseAndHierarchy);
  await runTest("Test 4: jobs", test4Jobs);
}

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

document.addEventListener("DOMContentLoaded", () => {
  $("apiBase").value = detectApiBase();

  $("btnDetect").addEventListener("click", () => {
    $("apiBase").value = detectApiBase();
    setStatus(`API Base を自動設定: ${getBase()}`, true);
  });

  $("btnHealth").addEventListener("click", runHealth);
  $("btnT1").addEventListener("click", () => runTest("Test 1: raw/scatter", test1PipelineAndScatter));
  $("btnT2").addEventListener("click", () => runTest("Test 2: cluster/hierarchy", test2ClusterAndHierarchy));
  $("btnT3").addEventListener("click", () => runTest("Test 3: dense/hierarchy", test3DenseAndHierarchy));
  $("btnT4").addEventListener("click", () => runTest("Test 4: jobs", test4Jobs));
  $("btnAll").addEventListener("click", runAll);
  $("btnClear").addEventListener("click", clearResults);
  $("btnSaveJson").addEventListener("click", saveJson);
  $("btnSaveTxt").addEventListener("click", saveTxt);

  setStatus(`準備完了: ${getBase()}`, true);
  writeLog("API tester initialized");
});
