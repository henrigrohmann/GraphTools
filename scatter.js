// @ts-nocheck
console.log("scatter.js loaded");

export function renderScatter(containerId, scatterData, onPointClick) {
  // x, y は必ず数値にする（string だと scattergl が止まる）
  const x = scatterData.map(d => Number(d.x));
  const y = scatterData.map(d => Number(d.y));
  const text = scatterData.map(d => d.text);

  // ★ cluster_id を正しく参照（ここが最重要）
  const cluster = scatterData.map(d => d.cluster_id);

  console.log("unique clusters =", [...new Set(cluster)]);

  // A/B/C → 色
  const clusterColors = {
    "A": "rgba(66, 135, 245, 0.8)",   // 青
    "B": "rgba(46, 204, 113, 0.8)",   // 緑
    "C": "rgba(231, 76, 60, 0.8)",    // 赤
    "Other": "rgba(149, 165, 166, 0.8)"
  };

  const colors = cluster.map(c => clusterColors[c] || clusterColors["Other"]);

  console.log("colors =", colors);

  const trace = {
    x,
    y,
    text,
    mode: "markers",
    type: "scattergl",
    marker: {
      size: 10,
      color: colors,
      line: { width: 1, color: "white" }
    },
    hovertemplate: "%{text}<extra></extra>",

    // customdata も安全に
    customdata: scatterData
  };

  const layout = {
    margin: { l: 0, r: 0, t: 0, b: 0 },
    xaxis: { scaleanchor: "y", showgrid: false, zeroline: false },
    yaxis: { showgrid: false, zeroline: false },
    paper_bgcolor: "#f7f7f7",
    plot_bgcolor: "#f7f7f7",
    dragmode: "pan"
  };

  Plotly.newPlot(containerId, [trace], layout, { responsive: true });

  const plot = document.getElementById(containerId);
  plot.on("plotly_click", ev => {
    const point = ev.points[0].customdata;
    onPointClick(point);
  });
}
