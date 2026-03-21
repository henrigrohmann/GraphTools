// ============================================================
// Utility
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

  return "http://127.0.0.1:8005";
}

function updateApiBaseDisplay() {
  const el = document.getElementById("api-base-text");
  if (el) el.textContent = detectApiBase();
}

function logMessage(message) {
  const panel = document.getElementById("log-panel");
  if (!panel) return;

  const time = new Date().toLocaleTimeString("ja-JP", { hour12: false });
  panel.textContent += `[${time}] ${message}\n`;
  panel.scrollTop = panel.scrollHeight;
}

function updateBreadcrumb(text) {
  const el = document.getElementById("breadcrumb-text");
  if (el) el.textContent = text;
}

async function fetchJson(path) {
  const url = `${detectApiBase()}${path}`;
  logMessage(`FETCH ${url}`);

  const res = await fetch(url);
  const text = await res.text();
  logMessage(`STATUS ${res.status} ${path}`);

  let json = {};
  if (text) {
    try {
      json = JSON.parse(text);
    } catch {
      throw new Error(`Invalid JSON: ${path}`);
    }
  }

  if (!res.ok) {
    const detail = json?.detail ? JSON.stringify(json.detail) : text.slice(0, 160);
    throw new Error(`HTTP ${res.status} ${path}: ${detail}`);
  }

  return json;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

// ============================================================
// Integration helpers
// ============================================================

async function checkHealth() {
  try {
    const payload = await fetchJson("/jobs");
    logMessage(`HEALTH OK jobs=${payload.count}`);
    updateBreadcrumb("ヘルスチェックOK");
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    logMessage(`HEALTH NG ${message}`);
    updateBreadcrumb("ヘルスチェックNG");
    const detail = document.getElementById("detail-content");
    if (detail) detail.textContent = `Health check failed: ${message}`;
  }
}

async function materializeMode(mode) {
  return fetchJson(`/${mode}`);
}

// ============================================================
// Scatter
// ============================================================

async function loadScatter(mode) {
  try {
    updateBreadcrumb(`散布図 (${mode})`);
    logMessage(`LOAD SCATTER ${mode}`);

    await materializeMode(mode);
    const json = await fetchJson(`/scatter?mode=${mode}`);

    const xs = json.data.map(item => item.x);
    const ys = json.data.map(item => item.y);
    const texts = json.data.map(item => item.summary || item.fullOpinion || "");
    const ids = json.data.map(item => item.id);

    const trace = {
      x: xs,
      y: ys,
      text: texts,
      customdata: ids,
      mode: "markers",
      type: "scatter",
      marker: { size: 8, color: "#0b66c3" },
    };

    await Plotly.newPlot("plot", [trace], {
      margin: { t: 20, r: 20, b: 40, l: 40 },
    });

    const plotDiv = document.getElementById("plot");
    plotDiv.on("plotly_click", event => {
      const point = event.points?.[0];
      if (!point) return;
      showDetail(point.customdata, point.text || "");
    });

    const hierarchyMode = mode === "cluster" ? "cluster" : mode === "dense" ? "dense" : "external";
    await loadHierarchy(hierarchyMode);
    logMessage(`SCATTER READY count=${json.count}`);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    logMessage(`SCATTER ERROR ${message}`);
    const detail = document.getElementById("detail-content");
    if (detail) detail.textContent = `Scatter load error: ${message}`;
  }
}

function showDetail(id, text) {
  updateBreadcrumb(`詳細 (${id})`);

  const el = document.getElementById("detail-content");
  if (!el) return;

  el.innerHTML = `
    <div><strong>ID:</strong> ${escapeHtml(id)}</div>
    <div style="margin-top: 6px;"><strong>内容:</strong><br/>${escapeHtml(text)}</div>
  `;
}

// ============================================================
// Hierarchy
// ============================================================

async function loadHierarchy(mode = "cluster") {
  const json = await fetchJson(`/hierarchy?mode=${mode}`);
  renderHierarchy(json.clusterList || [], json.argumentList || []);
  logMessage(`HIERARCHY READY mode=${mode} clusters=${json.clusterList?.length || 0}`);
}

function renderHierarchy(clusterList, argumentList) {
  const container = document.getElementById("hierarchy-content");
  if (!container) return;

  const argumentMap = new Map(argumentList.map(argument => [argument.id, argument]));

  function renderLegacyNode(id, depth) {
    const node = argumentMap.get(id);
    if (!node) return "";

    const indent = "&nbsp;".repeat(depth * 4);
    let html = `${indent}• ${escapeHtml(node.fullOpinion || node.summary || node.id)}<br/>`;
    if (Array.isArray(node.children)) {
      for (const childId of node.children) {
        html += renderLegacyNode(childId, depth + 1);
      }
    }
    return html;
  }

  function renderMembers(memberIds, depth) {
    const indent = "&nbsp;".repeat(depth * 4);
    let html = "";
    for (const memberId of memberIds) {
      const member = argumentMap.get(memberId);
      const text = member?.fullOpinion || member?.summary || memberId;
      html += `${indent}• ${escapeHtml(text)}<br/>`;
    }
    return html;
  }

  let html = "";
  for (const cluster of clusterList) {
    const title = cluster.label || cluster.summary || cluster.id;
    html += `<div style="margin-bottom: 8px;"><strong>${escapeHtml(title)}</strong><br/>`;
    if (Array.isArray(cluster.memberIds)) {
      html += renderMembers(cluster.memberIds, 1);
    } else {
      html += renderLegacyNode(cluster.id, 1);
    }
    html += "</div>";
  }

  container.innerHTML = html || "階層データはまだありません。";
}

// ============================================================
// Tabs
// ============================================================

function setupTabs() {
  const tabs = document.querySelectorAll(".tab-btn");
  const contents = document.querySelectorAll(".tab-content");

  for (const button of tabs) {
    button.addEventListener("click", () => {
      const tab = button.dataset.tab;
      for (const other of tabs) other.classList.remove("active");
      for (const content of contents) content.classList.remove("active");
      button.classList.add("active");
      document.getElementById(`tab-${tab}`)?.classList.add("active");
      updateBreadcrumb(tab === "detail" ? "詳細" : "階層ビュー");
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  updateApiBaseDisplay();
  setupTabs();
  loadScatter("cluster");
});

window.checkHealth = checkHealth;
window.loadScatter = loadScatter;

