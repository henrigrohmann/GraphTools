// @ts-nocheck
console.log("scatter.js loaded");

export function renderScatter(containerId, scatterData, onPointClick) {
  const x = scatterData.map(d => d.x);
  const y = scatterData.map(d => d.y);
  const text = scatterData.map(d => d.text);
  const cluster = scatterData.map(d => d.cluster);

  console.log("clusters (raw) =", cluster);
  console.log("unique clusters =", [...new Set(cluster)]);

  const clusterColors = {
    "Health": "rgba(66, 135, 245, 0.8)",
    "Rules":  "rgba(46, 204, 113, 0.8)",
    "Rights": "rgba(231, 76, 60, 0.8)",
    "Other":  "rgba(149, 165, 166, 0.8)"
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
      line: {
        width: 1,
        color: "white"
      }
    },
    hovertemplate: "%{text}<extra></extra>",
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
