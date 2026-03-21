// ============================================================
// Utility
// ============================================================
async function fetchJson(path) {
  const res = await fetch(`${detectApiBase()}${path}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
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

  return "http://127.0.0.1:8005";
}

// ============================================================
// Scatter Loader
// ============================================================
async function loadScatter(mode) {
  try {
    // Ensure the selected pipeline data is materialized before fetching scatter payload.
    await fetchJson(`/${mode}`);
    const json = await fetchJson(`/scatter?mode=${mode}`);

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

    // scatter 描画後に階層ビューも更新
    const hierarchyMode = mode === "dense" ? "dense" : (mode === "cluster" ? "cluster" : "external");
    loadHierarchy(hierarchyMode);

  } catch (e) {
    console.error("Scatter load error:", e);
    const detail = document.getElementById("detail-content");
    if (detail) {
      detail.textContent = `Scatter load error: ${e.message || e}`;
    }
  }
}

// ============================================================
// 詳細タブの描画
// ============================================================
function showDetail(id, text) {
  const el = document.getElementById("detail-content");
  if (!el) return;

  el.innerHTML = `
    <div><strong>ID:</strong> ${id}</div>
    <div style="margin-top:6px;"><strong>内容:</strong><br/>${text}</div>
  `;
}

// ============================================================
// 階層ビュー描画（最小版）
// ============================================================
function renderHierarchy(clusterList, argumentList) {
  const container = document.getElementById("hierarchy-content");
  if (!container) return;

  const map = {};
  argumentList.forEach(a => {
    map[a.id] = a;
  });

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

  let html = "";
  clusterList.forEach(c => {
    const title = c.label || c.summary || c.id;
    html += `<div style="margin-bottom:8px;"><strong>${title}</strong><br/>`;

    if (Array.isArray(c.memberIds)) {
      html += renderMemberList(c.memberIds, 1);
    } else {
      // Backward compatibility for old tree format where argument node links by children.
      html += renderLegacyNode(c.id, 1);
    }

    html += `</div>`;
  });

  container.innerHTML = html;
}

// ============================================================
// 階層データ読み込み
// ============================================================
async function loadHierarchy(mode = "cluster") {
  try {
    const json = await fetchJson(`/hierarchy?mode=${mode}`);
    renderHierarchy(json.clusterList, json.argumentList);
  } catch (e) {
    console.error("Hierarchy load error:", e);
  }
}

// ============================================================
// タブ切り替え
// ============================================================
document.addEventListener("DOMContentLoaded", () => {
  const tabButtons = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");

  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const target = btn.dataset.tab;

      tabButtons.forEach(b => b.classList.remove("active"));
      tabContents.forEach(c => c.classList.remove("active"));

      btn.classList.add("active");
      document.getElementById(`tab-${target}`).classList.add("active");
    });
  });

  // Initial render for first view.
  loadScatter("cluster");
});
