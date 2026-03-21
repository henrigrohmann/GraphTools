// ------------------------------
// API Utility
// ------------------------------
async function fetchJson(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
}

// ------------------------------
// Scatter Loader
// ------------------------------
async function loadScatter(mode) {
  try {
    const json = await fetchJson(`/scatter?mode=${mode}`);

    const xs = json.data.map(d => d.x);
    const ys = json.data.map(d => d.y);
    const texts = json.data.map(d => d.summary || d.fullOpinion || "");

    const trace = {
      x: xs,
      y: ys,
      text: texts,
      mode: "markers",
      type: "scatter",
      marker: { size: 8, color: "#0b66c3" }
    };

    Plotly.newPlot("plot", [trace], {
      margin: { t: 20, r: 20, b: 20, l: 20 }
    });

    // scatter 描画後に階層ビューも更新
    loadHierarchy("cluster");

  } catch (e) {
    console.error("Scatter load error:", e);
  }
}

// ------------------------------
// 階層ビュー描画（最小版）
// ------------------------------
function renderHierarchy(clusterList, argumentList) {
  const container = document.getElementById("hierarchy-content");
  if (!container) return;

  const map = {};
  argumentList.forEach(a => map[a.id] = a);

  function renderNode(id, depth = 0) {
    const node = map[id];
    if (!node) return "";

    const indent = "&nbsp;".repeat(depth * 4);
    let html = `${indent}• ${node.fullOpinion}<br/>`;

    if (Array.isArray(node.children)) {
      node.children.forEach(childId => {
        html += renderNode(childId, depth + 1);
      });
    }
    return html;
  }

  let html = "";
  clusterList.forEach(c => {
    html += `<div style="margin-bottom:8px;"><strong>${c.id}</strong><br/>`;
    html += renderNode(c.id, 1);
    html += `</div>`;
  });

  container.innerHTML = html;
}

// ------------------------------
// 階層データ読み込み
// ------------------------------
async function loadHierarchy(mode = "cluster") {
  try {
    const json = await fetchJson(`/hierarchy?mode=${mode}`);
    renderHierarchy(json.clusterList, json.argumentList);
  } catch (e) {
    console.error("Hierarchy load error:", e);
  }
}

// ------------------------------
// タブ切り替え
// ------------------------------
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
});
