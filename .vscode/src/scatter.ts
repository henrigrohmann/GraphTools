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
  // 3つの島（A/B/C）の中心
  const clusterCenters = {
    A: { x: -3, y: 2 },
    B: { x: -1, y: -2 },
    C: { x: 3,  y: 1 }
  };

  // カテゴリのサブクラスタ
  const subOffsets = {
    Health: { x: -0.4, y: 0.3 },
    Rules:  { x: 0.3,  y: -0.2 },
    Rights: { x: 0.1,  y: 0.4 }
  };

  const base = clusterCenters[op.group];
  const sub  = subOffsets[op.category];

  // 意見の長さで微妙に散らす + ノイズ
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

    // カテゴリ色
    colors.push(categoryColor[op.category]);

    // 意見の長さでサイズ変化（重みの表現）
    sizes.push(10 + op.fullOpinion.length * 0.02);
  }

  console.log("Scatter data generated.");

  return [
    // メインの散布図
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

    // クラスタ境界線（AI が空間を分割している感）
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
// Plotly イベント
// =======================================
window.attachPlotEvents = function (chartEl) {
  chartEl.on("plotly_click", function (data) {
    if (!data || !data.points || data.points.length === 0) return;

    const point = data.points[0];
    const id = point.customdata;

    console.log("Clicked point ID =", id);

    const detail = window.publicOpinionData.find(d => d.id === id);
    if (detail) {
      const panel = document.getElementById("detail-content");
      panel.textContent =
        `ID: ${detail.id}\n` +
        `Group: ${detail.group}\n` +
        `Category: ${detail.category}\n\n` +
        `${detail.fullOpinion}`;
    }
  });
};

console.log("scatter.js loaded (full enhanced version)");
