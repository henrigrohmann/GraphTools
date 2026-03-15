/* eslint-disable */
// @ts-nocheck

// =======================================
// GraphTool scatter.ts（完全統合版）
// =======================================

// カテゴリ色（視覚的に一瞬で理解できる）
const categoryColor = {
  Health: "#4C9AFF",   // 青
  Rules:  "#36B37E",   // 緑
  Rights: "#FF5630"    // 赤
};

// 微小ノイズ（散布図を“生きた”見た目にする）
function jitter(scale = 0.1) {
  return (Math.random() - 0.5) * scale;
}

// 疑似 k-means 風の座標生成（世界観調整済み）
function computeKMeansLikePosition(op) {
  const clusterCenters = {
    A: { x: -3, y: 2 },
    B: { x: -1, y: -2 },
    C: { x: 3,  y: 1 }
  };

  const subOffsets = {
    Health: { x: -0.4, y: 0.3 },
    Rules:  { x: 0.3,  y: -0.2 },
    Rights: { x: 0.1,  y: 0.4 }
  };

  const base = clusterCenters[op.group];
  const sub  = subOffsets[op.category];

  const x = base.x + sub.x + (op.opinion.length % 20) * 0.02 + jitter(0.15);
  const y = base.y + sub.y + (op.fullOpinion.length % 30) * 0.02 + jitter(0.15);

  return { x, y };
}

// =======================================
// Plotly 用データ生成
// =======================================
window.buildScatterData = function () {
  const xs = [];
  const ys = [];
  const ids = [];
  const texts = [];
  const colors = [];
  const sizes = [];

  for (const op of window.publicOpinionData) {
    const coords = computeKMeansLikePosition(op);

    xs.push(coords.x);
    ys.push(coords.y);
    ids.push(op.id);
    texts.push(op.opinion);

    colors.push(categoryColor[op.category]);
    sizes.push(10 + op.fullOpinion.length * 0.02);
  }

  console.log("Scatter data generated.");

  return [
    {
      x: xs,
      y: ys,
      mode: "markers",
      type: "scatter",
      marker: {
        size: sizes,
        color: colors,
        opacity: 0.75,
        line: { width: 1, color: "#333" }
      },
      customdata: ids,
      text: texts,
      hovertemplate: "%{text}<extra></extra>"
    },

    // クラスタ境界線
    {
      x: [-3, -1, 3, -3],
      y: [2, -2, 1, 2],
      mode: "lines",
      line: { color: "#999", dash: "dot", width: 1 },
      hoverinfo: "skip",
      showlegend: false
    }
  ];
};

// =======================================
// Plotly レイアウト
// =======================================
window.buildLayout = function () {
  return {
    title: "Public Opinion Map (K-means Inspired)",
    xaxis: { title: "Dimension 1", zeroline: false },
    yaxis: { title: "Dimension 2", zeroline: false },
    margin: { t: 40, l: 40, r: 20, b: 40 }
  };
};

// =======================================
// 右パネル UI 更新
// =======================================
let currentDetailId = null;

function updateDetailPanel(id) {
  currentDetailId = id;

  const detail = window.publicOpinionData.find(d => d.id === id);
  if (!detail) return;

  document.getElementById("detail-title").textContent = detail.opinion;

  const groupColor = { A: "#0052CC", B: "#5243AA", C: "#FF8B00" };

  const bg = document.getElementById("badge-group");
  bg.textContent = `Group: ${detail.group}`;
  bg.style.background = groupColor[detail.group];

  const bc = document.getElementById("badge-category");
  bc.textContent = detail.category;
  bc.style.background = categoryColor[detail.category];

  document.getElementById("detail-body").textContent = detail.fullOpinion;
}

function navigateDetail(offset) {
  if (currentDetailId === null) return;

  const newId = currentDetailId + offset;
  if (newId < 0 || newId >= window.publicOpinionData.length) return;

  updateDetailPanel(newId);
}

// =======================================
// Plotly イベント
// =======================================
window.attachPlotEvents = function (chartEl) {
  chartEl.on("plotly_click", function (data) {
    if (!data || !data.points || data.points.length === 0) return;

    const point = data.points[0];
    const id = point.customdata;

    console.log("Clicked point ID =", id);

    updateDetailPanel(id);
  });

  document.getElementById("prev-btn").onclick = () => navigateDetail(-1);
  document.getElementById("next-btn").onclick = () => navigateDetail(1);
};

console.log("scatter.js loaded (full enhanced version)");
