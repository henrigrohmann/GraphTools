console.log("scatter.js loaded");

window.buildScatterPlot = function(data) {
  const xs = data.points.map(p => p.x);
  const ys = data.points.map(p => p.y);
  const labels = data.points.map(p => p.text);
  const clusters = data.points.map(p => p.cluster);

  const trace = {
    x: xs,
    y: ys,
    text: labels,
    mode: "markers",
    type: "scattergl",
    marker: {
      size: 12,
      color: clusters,
      colorscale: "Viridis"
    }
  };

  const layout = {
    margin: { t: 20, r: 20, b: 40, l: 40 }
  };

  Plotly.newPlot("plot", [trace], layout);

  // クリックイベント → 右パネルに表示
  const plot = document.getElementById("plot");
  plot.on("plotly_click", function(ev) {
    const idx = ev.points[0].pointIndex;
    const text = data.points[idx].text;
    document.getElementById("opinion-text").textContent = text;
  });
};
