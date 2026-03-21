// ============================================================
// Utility
// ============================================================

// API Base を自動判定
function detectApiBase() {
  const paramBase = new URLSearchParams(window.location.search).get("apiBase");
  if (paramBase) return paramBase.replace(/\/$/, "");

  const origin = window.location.origin;

  // Codespaces
  if (origin.includes(".app.github.dev")) {
    return origin.replace(/-\d+\.app\.github\.dev$/, "-8005.app.github.dev");
  }

  // localhost
  if (/localhost|127\.0\.0\.1/.test(origin)) {
    return origin.replace(/:\d+$/, ":8005");
  }

  // fallback
  return "http://127.0.0.1:8005";
}

// API Base を画面に表示
function updateApiBaseDisplay() {
  const el = document.getElementById("api-base-text");
  if (el) el.textContent = detectApiBase();
}

// JSON fetch
async function fetchJson(path) {
  const url = `${detectApiBase()}${path}`;
  logMessage(`FETCH ${url}`);

  const res = await fetch(url);
  logMessage(` = status ${res.status}`);

  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
}

// ログ出力
function logMessage(msg) {
  const panel = document.getElementById("log-panel");
  if (!panel) return;

  const time = new Date().toLocaleTimeString();
  panel.textContent += `[${time}] ${msg}\n`;
  panel.scrollTop = panel.scrollHeight;
}

// パンくず更新
function updateBreadcrumb(text) {
  const el = document.getElementById("breadcrumb-text");
  if (el) el.textContent = text;
}
// ============================================================
// Scatter Loader
// ============================================================

async function loadScatter(mode) {
  try {
    updateBreadcrumb(`散布図（${mode}）`);
    logMessage(`LOAD SCATTER: ${mode}`);

    // パイプライン前処理（raw / cluster / dense など）
    await fetchJson(`/${mode}`);

    // 散布図データ取得
    const json = await fetchJson(`/scatter?mode=${mode}`);
    logMessage(`SCATTER READY: mode=${mode}, count=${json.data.length}`);

    const xs = json.data.map(d => d.x);
    const ys = json.data.map(d => d.y);
    const texts = json.data.map(d => d.summary || d.fullOpinion || "");
    const ids = json.data.map(d => d.id);

    const trace = {
      x: xs,
      y: ys,
      text: texts,
      customdata: ids,
      mode: "markers",
      type: "scatter",
      marker: { size: 8, color: "#0b66c3" }
    };

    Plotly.newPlot("plot", [trace], {
      margin: { t: 20, r: 20, b: 20, l: 20 }
    });

    // 点クリックイベント
    const plotDiv = document.getElementById("plot");
    plotDiv.on("plotly_click", (ev) => {
      const p = ev.points?.[0];
      if (!p) return;

      const id = p.customdata;
      const text = p.text || "";
      showDetail(id, text);
    });

    // 階層ビューも更新
    const hierarchyMode =
      mode === "dense" ? "dense" :
      mode === "cluster" ? "cluster" :
      "external";

    loadHierarchy(hierarchyMode);

  } catch (e) {
    logMessage(`Scatter load error: ${e.message}`);
    const detail = document.getElementById("detail-content");
    if (detail) {
      detail.textContent = `Scatter load error: ${e.message}`;
    }
  }
}

// ============================================================
// 詳細タブの描画（v1 仕様）
// ============================================================

function showDetail(id, text) {
  updateBreadcrumb(`詳細（ID: ${id}）`);

  const el = document.getElementById("detail-content");
  if (!el) return;

  el.innerHTML = `
    <div><strong>ID:</strong> ${id}</div>
    <div style="margin-top:6px;"><strong>内容:</strong><br/>${text}</div>
  `;
}
// ============================================================
// 階層ビュー描画（clusterList + argumentList）
// ============================================================

async function loadHierarchy(mode = "cluster") {
  try {
    updateBreadcrumb(`階層ビュー（${mode}）`);
    logMessage(`LOAD HIERARCHY: ${mode}`);

    const json = await fetchJson(`/hierarchy?mode=${mode}`);
    renderHierarchy(json.clusterList, json.argumentList);

  } catch (e) {
    logMessage(`Hierarchy load error: ${e.message}`);
    const el = document.getElementById("hierarchy-content");
    if (el) el.textContent = `Hierarchy load error: ${e.message}`;
  }
}

function renderHierarchy(clusterList, argumentList) {
  const container = document.getElementById("hierarchy-content");
  if (!container) return;

  const map = {};
  argumentList.forEach(a => {
    map[a.id] = a;
  });

  // 旧フォーマット（children）対応
  function renderLegacyNode(id, depth = 0) {
    const node = map[id];
    if (!node) return "";

    const indent = "&nbsp;".repeat(depth * 4);
    let html = `${indent}• ${node.fullOpinion || node.summary || node.id}<br/>`;

    if (Array.isArray(node.children)) {
      node.children.forEach(childId => {
        html += renderLegacyNode(childId, depth + 1);
      });
    }
    return html;
  }

  // 新フォーマット（memberIds）対応
  function renderMemberList(memberIds, depth = 1) {
    const indent = "&nbsp;".repeat(depth * 4);
    let html = "";

    memberIds.forEach(memberId => {
      const member = map[memberId];
      const text = member?.fullOpinion || member?.summary || memberId;
      html += `${indent}• ${text}<br/>`;
    });

    return html;
  }

  // clusterList を描画
  let html = "";
  clusterList.forEach(c => {
    const title = c.label || c.summary || c.id;
    html += `<div style="margin-bottom:8px;"><strong>${title}</strong><br/>`;

    if (Array.isArray(c.memberIds)) {
      html += renderMemberList(c.memberIds, 1);
    } else {
      html += renderLegacyNode(c.id, 1);
    }

    html += `</div>`;
  });

  container.innerHTML = html;
}
// ============================================================
// タブ切り替え（詳細 / 階層ビュー）
// ============================================================

function setupTabs() {
  const tabs = document.querySelectorAll(".tab-btn");
  const contents = document.querySelectorAll(".tab-content");

  tabs.forEach(btn => {
    btn.addEventListener("click", () => {
      const tab = btn.dataset.tab;

      // ボタンの active 切り替え
      tabs.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");

      // コンテンツの active 切り替え
      contents.forEach(c => c.classList.remove("active"));
      document.getElementById(`tab-${tab}`).classList.add("active");

      // パンくず更新
      if (tab === "detail") {
        updateBreadcrumb
