// ===============================
// API 呼び出し
// ===============================

async function runPipeline(mode) {
  const statusEl = document.getElementById("status");
  statusEl.textContent = `Running ${mode} pipeline...`;

  try {
    // 1. パイプライン実行
    const res1 = await fetch(`/${mode}`);
    const json1 = await res1.json();

    statusEl.textContent = `Pipeline done. Loading scatter data...`;

    // 2. scatter データ取得
    const res2 = await fetch(`/scatter?mode=${mode}`);
    const json2 = await res2.json();

    statusEl.textContent = `Rendering scatter (${json2.count} points)...`;

    // 3. 描画
    renderScatter(json2.data, mode);

    statusEl.textContent = `Done (${mode}).`;
  } catch (err) {
    statusEl.textContent = `Error: ${err}`;
  }
}


// ===============================
// Plotly 描画
// ===============================

function renderScatter(data, mode) {
  const xs = data.map(d => d.x);
  const ys = data.map(d => d.y);
  const texts = data.map(d => `${d.id}: ${d.summary}`);

  // cluster のときだけ色分け
  let colors = "black";
  if (mode === "cluster") {
    colors = data.map(d => {
      if (d.cluster_id === "A") return "red";
      if (d.cluster_id === "B") return "blue";
      if (d.cluster_id === "C") return "green";
      return "gray";
    });
  }

  const trace = {
    x: xs,
    y: ys,
    mode: "markers",
    type: "scattergl",
    marker: {
      size: 10,
      color: colors,
    },
    text: texts,
    hovertemplate: "%{text}<extra></extra>"
  };

  const layout = {
    title: `Scatter (${mode})`,
    xaxis: { title: "X" },
    yaxis: { title: "Y" }
  };

  Plotly.newPlot("chart", [trace], layout);
}
