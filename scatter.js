// @ts-nocheck
console.log("scatter.js loaded (UI LOG MODE)");

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

// ★ window に登録（最重要）
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
  uiLog("unique clusters", [...new Set(cluster)]);

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
    type: "scatter", // ★ まずは Canvas で安定運用
    marker: {
      size: 10,
      color: colors,
      line: { width: 1, color: "white" }
    },
    hovertemplate: "%{text}<extra></extra>",
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
    onPointClick(point);
  });
};
