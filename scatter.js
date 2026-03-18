// ===============================
// API ベース URL（あなたの Codespaces 8001）
// ===============================
const API_BASE = "https://didactic-parakeet-xgrr599556rhpx65-8001.app.github.dev";


// ===============================
// デバッグログ
// ===============================
function logDebug(msg) {
  const panel = document.getElementById("debug-panel");
  const time = new Date().toLocaleTimeString();
  panel.textContent += `[${time}] ${msg}\n`;
  panel.scrollTop = panel.scrollHeight;
}

logDebug("scatter.js loaded");


// ===============================
// API 呼び出し
// ===============================
async function runPipeline(mode) {
  const statusEl = document.getElementById("status");
  statusEl.textContent = `Running ${mode} pipeline...`;
  logDebug(`--- RUN PIPELINE: ${mode} ---`);

  try {
    // 1. パイプライン実行
    const url1 = `${API_BASE}/${mode}`;
    logDebug(`Calling ${url1}`);
    const res1 = await fetch(url1);
    const json1 = await res1.json();
    logDebug(`Pipeline result: ${JSON.stringify(json1)}`);

    statusEl.textContent = `Pipeline done. Loading scatter data...`;

    // 2. scatter データ取得
    const url2 = `${API_BASE}/scatter?mode=${mode}`;
    logDebug(`Calling ${url2}`);
    const res2 = await fetch(url2);
    const json2 = await res2.json();
    logDebug(`Scatter count: ${json2.count}`);

    statusEl.textContent = `Rendering scatter (${json2.count} points)...`;

    // 3. 描画
    renderScatter(json2.data, mode);

    statusEl.textContent = `Done (${mode}).`;
    logDebug(`Render complete.`);

  } catch (err) {
    statusEl.textContent = `Error: ${err}`;
    logDebug(`ERROR: ${err}`);
  }
}


// ===============================
// Plotly 描画
// ===============================
function renderScatter(data, mode) {
  logDebug(`Rendering scatter: mode=${mode}, points=${data.length}`);

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
