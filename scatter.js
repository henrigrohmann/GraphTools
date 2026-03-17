// @ts-nocheck
console.log("scatter.js loaded");

// Plotly の描画関数
export function renderScatter(containerId, scatterData, onPointClick) {
  const x = scatterData.map(d => d.x);
  const y = scatterData.map(d => d.y);
  const text = scatterData.map(d => d.text);
  const cluster = scatterData.map(d => d.cluster);

  // カラーリング（あなたの Monday Night カラー）
  const clusterColors = {
    "Health": "rgba(66, 135, 245, 0.8)",   // 青
    "Rules":  "rgba(46, 204, 113, 0.8)",   // 緑
    "Rights": "rgba(231, 76, 60, 0.8)",    // 赤
    "Other":  "rgba(149, 165, 166, 0.8)"   // グレー
  };

  const colors = cluster.map(c => clusterColors[c] || clusterColors["Other"]);

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
        color: "white"   // 境界線で視認性UP
      }
    },

    // hover を美しく
    hovertemplate: "%{text}<extra></extra>",

    // パネル連動用
    customdata: scatterData
  };

  const layout = {
    margin: { l: 0, r: 0, t: 0, b: 0 },

    // 正方形で安定
    xaxis: { scaleanchor: "y", showgrid: false, zeroline: false },
    yaxis: { showgrid: false, zeroline: false },

    // 背景を薄いグレーにして“地図感”
    paper_bgcolor: "#f7f7f7",
    plot_bgcolor: "#f7f7f7",

    dragmode: "pan"
  };

  Plotly.newPlot(containerId, [trace], layout, { responsive: true });

  // クリック → パネル連動
  const plot = document.getElementById(containerId);
  plot.on("plotly_click", ev => {
    const point = ev.points[0].customdata;
    onPointClick(point);
  });

  // hover 時に点を強調（size +2）
  plot.on("plotly_hover", ev => {
    Plotly.restyle(containerId, {
      "marker.size": 12,
      "marker.opacity": 1.0
    }, [ev.points[0].pointIndex]);
  });

  plot.on("plotly_unhover", ev => {
    Plotly.restyle(containerId, {
      "marker.size": 10,
      "marker.opacity": 0.8
    }, [ev.points[0].pointIndex]);
  });
}
