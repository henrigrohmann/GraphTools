// @ts-nocheck
console.log("scatter.js loaded (FILE LOG MODE)");

export function renderScatter(containerId, scatterData, onPointClick) {
  const fs = window.require ? window.require("fs") : null;

  function writeLog(label, data) {
    if (!fs) {
      console.warn("fs not available in browser");
      return;
    }
    const log = `\n=== ${label} ===\n${JSON.stringify(data, null, 2)}\n`;
    fs.appendFileSync("/workspaces/GraphTools/scatter.log", log);
  }

  writeLog("RAW scatterData", scatterData);

  const x = scatterData.map(d => Number(d.x));
  const y = scatterData.map(d => Number(d.y));
  const text = scatterData.map(d => d.text);
  const cluster = scatterData.map(d => d.cluster_id);

  writeLog("Parsed x", x);
  writeLog("Parsed y", y);
  writeLog("Parsed text", text);
  writeLog("Parsed cluster", cluster);

  const clusterColors = {
    "A": "rgba(66, 135, 245, 0.8)",
    "B": "rgba(46, 204, 113, 0.8)",
    "C": "rgba(231, 76, 60, 0.8)",
    "Other": "rgba(149, 165, 166, 0.8)"
  };

  const colors = cluster.map(c => clusterColors[c] || clusterColors["Other"]);
  writeLog("colors", colors);

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

  writeLog("TRACE", trace);

  const layout = {
    margin: { l: 0, r: 0, t: 0, b: 0 },
    xaxis: { showgrid: false, zeroline: false },
    yaxis: { showgrid: false, zeroline: false },
    paper_bgcolor: "#f7f7f7",
    plot_bgcolor: "#f7f7f7",
    dragmode: "pan"
  };

  writeLog("LAYOUT", layout);

  const config = {
    responsive: true,
    displayModeBar: false
  };

  writeLog("CONFIG", config);

  writeLog("STATUS", "Calling Plotly.newPlot");

  Plotly.newPlot(containerId, [trace], layout, config)
    .then(() => writeLog("STATUS", "Plotly.newPlot SUCCESS"))
    .catch(err => writeLog("ERROR", err));
}
