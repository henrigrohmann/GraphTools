// ============================================================
// GraphTool v1.8.2 フロントエンド（charts）
// ============================================================

let currentMode = "cluster";
let lastScatterData = [];

// ============================================================
// Utility
// ============================================================

// ★★★ Codespaces 8002 → 8005 を確実に変換し、Windows では誤作動しない最終版 ★★★
function detectApiBase() {
  const url = new URL(window.location.href);
  const host = url.hostname;

  // Codespaces: xxxxx-<port>.app.github.dev → xxxxx-8005.app.github.dev
  const m = host.match(/-(\d+)\.app\.github\.dev$/);
  if (m) {
    return `${url.protocol}//${host.replace(/-\d+\.app\.github\.dev$/, "-8005.app.github.dev")}`;
  }

  // ローカル Windows / macOS / Linux
  if (host === "localhost" || host === "127.0.0.1") {
    return `${url.protocol}//${host}:8005`;
  }

  // 本番環境
  return `${url.protocol}//${host}`;
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

function updateBreadcrumb(pathArray) {
  const wrapper = document.getElementById("breadcrumb-wrapper");
  const el = document.getElementById("breadcrumb-text");
  if (!wrapper || !el) return;

  if (!pathArray || pathArray.length === 0) {
    wrapper.classList.add("hidden");
    el.textContent = "";
    return;
  }

  wrapper.classList.remove("hidden");
  el.textContent = pathArray.join(" / ");
}

function updateModeText(mode) {
  const el = document.getElementById("mode-text");
  if (el) el.textContent = mode;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function normalizeScatterPoint(p) {
  return {
    ...p,
    clusterId: p.cluster_id ?? p.clusterId ?? "unassigned",
    summary: p.summary ?? "",
    title: p.title ?? "",
  };
}

// ============================================================
// fetchJson / postJson
// ============================================================

async function fetchJson(path) {
  const url = `${detectApiBase()}${path}`;
  logMessage(`FETCH ${url}`);

  const res = await fetch(url);
  const text = await res.text();
  logMessage(`STATUS ${res.status} ${path}`);

  let json = {};
  if (text) {
    try { json = JSON.parse(text); } catch {
      throw new Error(`Invalid JSON: ${path}`);
    }
  }
  if (!res.ok) {
    const detail = json?.detail ? JSON.stringify(json.detail) : text.slice(0, 160);
    throw new Error(`HTTP ${res.status} ${path}: ${detail}`);
  }
  return json;
}

async function postJson(path, body = {}) {
  const url = `${detectApiBase()}${path}`;
  logMessage(`POST ${url}`);

  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const text = await res.text();
  logMessage(`STATUS ${res.status} ${path}`);

  let json = {};
  if (text) {
    try { json = JSON.parse(text); } catch {
      throw new Error(`Invalid JSON: ${path}`);
    }
  }
  if (!res.ok) {
    const detail = json?.detail ? JSON.stringify(json.detail) : text.slice(0, 160);
    throw new Error(`HTTP ${res.status} ${path}: ${detail}`);
  }
  return json;
}

// ============================================================
// Scatter / Treemap
// ============================================================

const CLUSTER_COLORS = [
  "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
  "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
  "#bcbd22", "#17becf"
];

function denseColor(ratio) {
  const v = Math.max(0, Math.min(1, ratio));
  const r = Math.floor(255 * v);
  const b = Math.floor(255 * (1 - v));
  return `rgb(${r},0,${b})`;
}

async function loadScatter(mode) {
  currentMode = mode;
  updateModeText(mode);

  const breadcrumbMap = {
    raw: ["散布図", "生データ"],
    cluster: ["散布図", "クラスタリング"],
    dense: ["散布図", "濃い意見"],
    treemap: ["ツリーマップ"],
  };
  updateBreadcrumb(breadcrumbMap[mode] || ["散布図"]);

  try {
    if (mode === "treemap") {
      logMessage("LOAD TREEMAP");
      const raw = await fetchJson("/scatter?mode=cluster");
      const data = raw.map(normalizeScatterPoint);
      lastScatterData = data;
      await renderTreemap(data);
      await loadHierarchy("cluster");
      return;
    }

    logMessage(`LOAD SCATTER ${mode}`);
    const raw = await fetchJson(`/scatter?mode=${mode}`);
    const data = raw.map(normalizeScatterPoint);
    lastScatterData = data;

    await renderScatterFromData(data, mode);
    await loadHierarchy(mode === "raw" ? "cluster" : mode);
    logMessage(`SCATTER READY count=${data.length}`);

  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    logMessage(`SCATTER ERROR ${message}`);
    const detail = document.getElementById("detail-content");
    if (detail) detail.textContent = `Error: ${message}`;
  }
}

async function renderScatterFromData(data, modeLabel) {
  updateModeText(modeLabel);

  const clusterIds = [...new Set(data.map(p => p.clusterId))].sort();
  const clusterIndexMap = new Map(clusterIds.map((id, i) => [id, i]));

  let colors, sizes;
  if (modeLabel === "cluster" || modeLabel.startsWith("filter-")) {
    colors = data.map(p => CLUSTER_COLORS[clusterIndexMap.get(p.clusterId) % CLUSTER_COLORS.length]);
    sizes = data.map(() => 10);
  } else if (modeLabel === "dense") {
    const maxDist = Math.max(1, ...data.map(p => Math.sqrt(p.x * p.x + p.y * p.y)));
    colors = data.map(p => denseColor(Math.sqrt(p.x * p.x + p.y * p.y) / maxDist));
    sizes = data.map(p => 6 + Math.floor((Math.sqrt(p.x * p.x + p.y * p.y) / maxDist) * 14));
  } else {
    colors = data.map(() => "#888888");
    sizes = data.map(() => 8);
  }

  const trace = {
    x: data.map(p => p.x),
    y: data.map(p => p.y),
    text: data.map(p => p.summary),
    customdata: data,
    mode: "markers",
    type: "scatter",
    hovertemplate: "%{text}<extra></extra>",
    marker: { size: sizes, color: colors, opacity: 0.85 },
  };

  const plotEl = document.getElementById("plot");

  await Plotly.newPlot(plotEl, [trace], {
    margin: { t: 20, r: 20, b: 40, l: 40 },
  });

  plotEl.on("plotly_click", ev => {
    const point = ev.points?.[0];
    if (!point) return;
    showDetail(point.customdata);
  });
}

async function renderTreemap(data) {
  const clusterIds = [...new Set(data.map(p => p.clusterId))].sort();
  const ids = ["root"];
  const labels = ["全体"];
  const parents = [""];
  const values = [data.length];

  for (const cid of clusterIds) {
    ids.push(`cluster-${cid}`);
    labels.push(cid);
    parents.push("root");
    const members = data.filter(p => p.clusterId === cid);
    values.push(members.length);
    for (const p of members) {
      ids.push(p.id);
      labels.push(p.summary || p.id);
      parents.push(`cluster-${cid}`);
      values.push(1);
    }
  }

  await Plotly.newPlot("plot", [{
    type: "treemap",
    ids, labels, parents, values,
    textinfo: "label+value",
  }], {
    margin: { t: 20, r: 20, b: 20, l: 20 },
  });

  logMessage(`TREEMAP READY clusters=${clusterIds.length} total=${data.length}`);
}

// ============================================================
// 詳細パネル
// ============================================================

function showDetail(point) {
  if (!point) return;
  updateBreadcrumb(["詳細", point.id || ""]);
  const el = document.getElementById("detail-content");
  if (!el) return;
  el.innerHTML = `
    <div><strong>ID:</strong> ${escapeHtml(point.id || "")}</div>
    <div style="margin-top:6px;"><strong>summary:</strong><br>${escapeHtml(point.summary || "")}</div>
    <div style="margin-top:6px;"><strong>title:</strong><br>${escapeHtml(point.title || "")}</div>
    <div style="margin-top:6px;"><strong>clusterId:</strong> ${escapeHtml(point.clusterId || "")}</div>
  `;
}

// ============================================================
// 階層ビュー
// ============================================================

async function loadHierarchy(mode = "cluster") {
  try {
    const obj = await fetchJson(`/hierarchy?mode=${mode}`);
    logMessage(`HIERARCHY FETCH mode=${mode}`);

    if (!obj) {
      renderHierarchy([], []);
      return;
    }

    const clusterList = obj.clusterList || [];
    const argumentList = obj.argumentList || [];

    renderHierarchy(clusterList, argumentList);
    logMessage(`HIERARCHY READY clusters=${clusterList.length} args=${argumentList.length}`);

  } catch (e) {
    logMessage(`HIERARCHY ERROR ${e instanceof Error ? e.message : String(e)}`);
    const container = document.getElementById("hierarchy-content");
    if (container) container.textContent = "階層データの取得に失敗しました。";
  }
}

function renderHierarchy(clusterList, argumentList) {
  const container = document.getElementById("hierarchy-content");
  if (!container) return;

  const argumentMap = new Map(argumentList.map(a => [a.id, a]));
  let html = "";

  for (const cluster of clusterList) {
    const title = cluster.label || cluster.id;
    html += `<div style="margin-bottom:8px;"><strong>${escapeHtml(title)}</strong><br/>`;
    if (Array.isArray(cluster.memberIds)) {
      for (const memberId of cluster.memberIds) {
        const member = argumentMap.get(memberId);
        const text = member?.summary || member?.fullOpinion || memberId;
        html += `&nbsp;&nbsp;&nbsp;&nbsp;• ${escapeHtml(text)}<br/>`;
      }
    }
    html += "</div>";
  }

  container.innerHTML = html || "階層データはまだありません。";
}

// ============================================================
// フィルタ（cluster）
// ============================================================

async function filterCluster() {
  const cluster = prompt("クラスタIDを入力してください（例: A）");
  if (!cluster) return;

  try {
    logMessage(`FILTER cluster=${cluster}`);
    const raw = await fetchJson(`/filter?cluster=${encodeURIComponent(cluster)}`);
    const data = raw.map(normalizeScatterPoint);
    lastScatterData = data;

    updateBreadcrumb(["散布図", `フィルタ(${cluster})`]);
    await renderScatterFromData(data, `filter-${cluster}`);
    await loadHierarchy("cluster");

  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    logMessage(`FILTER ERROR ${message}`);
  }
}

// ============================================================
// デフォルトデータ読み込み
// ============================================================

async function loadDefault() {
  try {
    logMessage("DEFAULT LOAD start");
    updateBreadcrumb(["デフォルトデータ"]);

    await postJson("/init");
    logMessage("DEFAULT LOAD done");

    const detail = document.getElementById("detail-content");
    if (detail) {
      detail.innerHTML = `<strong>デフォルトデータ読み込み完了</strong>`;
    }

    await refreshScatterAndHierarchy();

  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    logMessage(`DEFAULT LOAD ERROR ${message}`);
  }
}

// ============================================================
// CSV アップロード
// ============================================================

async function uploadCSV() {
  const input = document.getElementById("csvFile");
  if (!input || !input.files || input.files.length === 0) {
    alert("CSVファイルを選択してください。");
    return;
  }

  const file = input.files[0];
  const form = new FormData();
  form.append("file", file);

  try {
    logMessage(`UPLOAD start file=${file.name}`);
    updateBreadcrumb(["CSVアップロード"]);

    const url = `${detectApiBase()}/upload`;
    const res = await fetch(url, { method: "POST", body: form });
    const text = await res.text();
    logMessage(`STATUS ${res.status} /upload`);

    if (!res.ok) {
      throw new Error(`Upload failed: ${text.slice(0, 200)}`);
    }

    const detail = document.getElementById("detail-content");
    if (detail) {
      detail.innerHTML = `<strong>CSVアップロード完了</strong><br/>${escapeHtml(file.name)}`;
    }

    await refreshScatterAndHierarchy();

  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    logMessage(`UPLOAD ERROR ${message}`);
  }
}

// ============================================================
// 共通：scatter + hierarchy 再読み込み
// ============================================================

async function refreshScatterAndHierarchy() {
  await loadScatter("raw");
  await loadHierarchy("cluster");
}

// ============================================================
// ダンプ / ヘルスチェック
// ============================================================

async function dumpData() {
  try {
    logMessage("DUMP start");
    updateBreadcrumb(["ダンプ"]);
    const payload = await fetchJson("/dump");

    const detail = document.getElementById("detail-content");
    if (detail) {
      detail.innerHTML =
        `<strong>テーブル件数</strong><br/>` +
        Object.entries(payload.tables || {})
          .map(([k, v]) => `${escapeHtml(k)}: ${v}`)
          .join("<br/>") +
        `<br/><br/><strong>階層JSON</strong><br/>` +
        escapeHtml(JSON.stringify(payload.hierarchy || {}, null, 2));
    }

    logMessage(`DUMP done`);

  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    logMessage(`DUMP ERROR ${message}`);
  }
}

async function checkHealth() {
  try {
    logMessage("HEALTH start");
    updateBreadcrumb(["ヘルスチェック"]);
    const payload = await fetchJson("/health");

    logMessage(`HEALTH OK status=${payload.status}`);
    const detail = document.getElementById("detail-content");
    if (detail) {
      detail.innerHTML =
        `<strong>Health</strong><br/>` +
        `status: ${escapeHtml(payload.status)}`;
    }

  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    logMessage(`HEALTH NG ${message}`);
    updateBreadcrumb(["ヘルスチェック", "NG"]);
    const detail = document.getElementById("detail-content");
    if (detail) detail.textContent = `Health check failed: ${message}`;
  }
}

// ============================================================
// ログパネル折りたたみ
// ============================================================

function toggleLogPanel() {
  const panel = document.getElementById("log-panel");
  const btn = document.getElementById("toggle-log");
  if (!panel || !btn) return;

  panel.classList.toggle("collapsed");
  btn.textContent = panel.classList.contains("collapsed") ? "▼" : "▲";
}

// ============================================================
// Tabs / 初期化
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
      updateBreadcrumb(tab === "detail" ? ["詳細"] : ["階層ビュー"]);
    });
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  updateApiBaseDisplay();
  setupTabs();
  updateBreadcrumb([]);
  updateModeText("-");
  logMessage("GraphTool v1.8.2 ready");
});
