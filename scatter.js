// @ts-nocheck
console.log("scatter.js loaded (FULL DEBUG)");

export function renderScatter(containerId, scatterData, onPointClick) {
  console.log("=== RAW scatterData ===");
  console.log(scatterData);

  // x, y は必ず数値に変換
  const x = scatterData.map(d => Number(d.x));
  const y = scatterData.map(d => Number(d.y));
  const text = scatterData.map(d => d.text);
  const cluster = scatterData.map(d => d.cluster_id);

  console.log("=== Parsed arrays ===");
  console.log("x:", x);
  console.log("y:", y);
  console.log("text:", text);
  console.log("cluster:", cluster);
  console.log("unique clusters:", [...new Set(cluster)]);

  // 色マップ
  const clusterColors = {
    "A": "rgba(66, 135, 245, 0.8)",
    "B": "rgba(46, 204, 113, 0.8)",
    "C": "rgba(231, 76, 60, 0.8)",
    "Other": "rgba(149, 165, 166, 0.8)"
  };

  const colors = cluster.map(c => clusterColors[c] || clusterColors["Other"]);
  console.log("colors:", colors);

  // trace
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
    customdata: scatterData
  };

  console.log("=== TRACE (to Plotly) ===");
  console.log(JSON.stringify(trace, null, 2));

  // layout
  const layout = {
    margin: { l: 0, r: 0, t: 0, b: 0 },
    xaxis: {
      showgrid: false,
      zeroline: false,
      title: "X",
      automargin: true
    },
    yaxis: {
      showgrid: false,
      zeroline: false,
      title: "Y",
      automargin: true
    },
    paper_bgcolor: "#f7f7f7",
    plot_bgcolor: "#f7f7f7",
    dragmode: "pan"
  };

  console.log("=== LAYOUT (to Plotly) ===");
  console.log(JSON.stringify(layout, null, 2));

  // config
  const config = {
    responsive: true,
    displayModeBar: false
  };

  console.log("=== CONFIG (to Plotly) ===");
  console.log(JSON.stringify(config, null, 2));

  console.log("=== Calling Plotly.newPlot ===");

  Plotly.newPlot(containerId, [trace], layout, config)
    .then(() => console.log("Plotly.newPlot: SUCCESS"))
    .catch(err => console.error("Plotly.newPlot: ERROR", err));

  const plot = document.getElementById(containerId);
  if (!plot) {
    console.error("ERROR: containerId not found:", containerId);
    return;
  }

  plot.on("plotly_click", ev => {
    const point = ev.points[0].customdata;
    onPointClick(point);
  });
}
