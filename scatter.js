// @ts-nocheck
console.log("scatter.js loaded (UI LOG MODE + enhanced right panel)");

function uiLog(label, data) {
  const panel = document.getElementById("log-panel");
  if (!panel) return;

  const block = document.createElement("div");
  block.style.borderTop = "1px solid #ddd";
  block.style.marginTop = "4px";
  block.style.paddingTop = "4px";

  const title = document.createElement("div");
  title.textContent = `=== ${label} ===`;
  title.style.fontWeight = "bold";

  const pre = document.createElement("pre");
  pre.textContent =
    typeof data === "string" ? data : JSON.stringify(data, null, 2);

  block.appendChild(title);
  block.appendChild(pre);
  panel.appendChild(block);
}

// ★ 右パネル更新（強化版）
function updateRightPanel(point) {
  const panel = document.getElementById("right-panel");
  if (!panel) return;

  const clusterColors = {
    A: "#4287f5",
    B: "#2ecc71",
    C: "#e74c3c",
    Other: "#7f8c8d"
  };

  const color = clusterColors[point.cluster_id] || clusterColors.Other;

  panel.style.opacity = 0; // フェードイン準備

  panel.innerHTML = `
    <div style="
      border-left: 6px solid ${color};
      padding-left: 12px;
      margin-bottom: 12px;
      font-weight: bold;
      font-size: 16px;
    ">
      意見 ID: ${point.id}
    </div>

    <div style="color:#666; margin-bottom: 8px;">
      クラスター: <b>${point.cluster_id}</b><br>
      座標: (${point.x}, ${point.y})
    </div>

    <div style="
      background: #fff;
      padding: 14px;
      border-radius: 6px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.08);
      border: 1px solid #eee;
      white-space: pre-wrap;
      font-size: 15px;
      line-height: 1.7;
    ">
      ${point.text}
    </div>
  `;

  // フェードイン
  setTimeout(() => {
    panel.style.transition = "opacity 0.25s ease";
    panel.style.opacity = 1;
  }, 10);
}

// ★ window に登録
window.renderScatter = function(containerId, scatterData, onPointClick) {
  uiLog("RAW scatterData", scatterData);

  const x = scatterData.map(d => Number(d.x));
  const y = scatterData.map(d => Number(d.y));
  const text = scatterData.map(d => d.text);
  const cluster = scatterData.map(d => d.cluster_id);

  uiLog("x", x);
  uiLog("y", y);
  uiLog("text", text);
  uiLog("cluster", cluster);

  const clusterColors = {
    A: "rgba(66, 135, 245, 0.9)",
    B: "rgba(46, 204, 113, 0.9)",
    C: "rgba(231, 76, 60, 0.9)",
    Other: "rgba(149, 165, 166, 0.9)"
  };

  const colors = cluster.map(c => clusterColors[c] || clusterColors.Other);
  uiLog("colors", colors);

  const trace = {
    x,
    y,
    text,
    mode: "markers",
    type: "scatter",
    marker: {
      size: 10,
      color: colors,
      line: { width: 1, color: "white" }
    },

    hovertemplate:
      "<div style='max-width:220px; line-height:1.4; white-space:normal;'>%{text}</div><extra></extra>",

    hoverlabel: {
      bgcolor: "white",
      bordercolor: "rgba(0,0,0,0.15)",
      font: { size: 13, color: "#333" },
      namelength: -1
    },

    customdata: scatterData
  };

  uiLog("TRACE", trace);

  const layout = {
    margin: { l: 0, r: 0, t: 0, b: 0 },
    xaxis: { showgrid: false, zeroline: false },
    yaxis: { showgrid: false, zeroline: false },
    paper_bgcolor: "#f7f7f7",
    plot_bgcolor: "#f7f7f7",
    dragmode: "pan"
  };

  uiLog("LAYOUT", layout);

  const config = {
    responsive: true,
    displayModeBar: false
  };

  uiLog("CONFIG", config);

  const el = document.getElementById(containerId);
  if (!el) {
    uiLog("ERROR", `containerId '${containerId}' not found`);
    return;
  }

  Plotly.newPlot(containerId, [trace], layout, config)
    .then(() => uiLog("STATUS", "Plotly.newPlot SUCCESS"))
    .catch(err => uiLog("ERROR Plotly.newPlot", String(err)));

  el.on("plotly_click", ev => {
    const point = ev.points[0].customdata;
    uiLog("CLICK point", point);

    updateRightPanel(point);

    onPointClick(point);
  });
};
