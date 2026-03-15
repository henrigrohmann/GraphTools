/* eslint-disable */
// @ts-nocheck

// =======================================
// GraphTool scatter.ts（K-means inspired）
// =======================================

// 疑似 k-means 風の座標生成
function computeKMeansLikePosition(op: any) {
  const clusterCenters: any = {
    A: { x: -2, y: 1 },
    B: { x: 0,  y: -1 },
    C: { x: 2,  y: 1 }
  };

  const subOffsets: any = {
    Health: { x: -0.4, y: 0.3 },
    Rules:  { x: 0.3,  y: -0.2 },
    Rights: { x: 0.1,  y: 0.4 }
  };

  const base = clusterCenters[op.group];
  const sub  = subOffsets[op.category];

  // クラスタ中心 + サブクラスタ + 微小な散らばり
  const x = base.x + sub.x + (op.opinion.length % 20) * 0.02;
  const y = base.y + sub.y + (op.fullOpinion.length % 30) * 0.02;

  return { x, y };
}

// =======================================
// Plotly 用データ生成
// =======================================
window.buildScatterData = function () {
  const xs: number[] = [];
  const ys: number[] = [];
  const ids: number[] = [];
  const texts: string[] = [];

  if (!window.publicOpinionData) {
    console.log("publicOpinionData is undefined in buildScatterData()");
    return [];
  }

  for (const op of window.publicOpinionData) {
    const coords = computeKMeansLikePosition(op);
    xs.push(coords.x);
    ys.push(coords.y);
    ids.push(op.id);
    texts.push(op.opinion);
  }

  console.log("Scatter data generated.");

  return [
    {
      x: xs,
      y: ys,
      mode: "markers",
      type: "scatter",
      marker: {
        size: 12,
        color: ids,
        colorscale: "Viridis"
      },
      customdata: ids,
      text: texts,
      hovertemplate: "%{text}<extra></extra>"
    }
  ];
};

// =======================================
// Plotly レイアウト
// =======================================
window.buildLayout = function () {
  return {
    title: "Public Opinion Scatter (K-means Inspired)",
    xaxis: { title: "Dimension 1" },
    yaxis: { title: "Dimension 2" },
    margin: { t: 40, l: 40, r: 20, b: 40 }
  };
};

// =======================================
// Plotly イベント
// =======================================
window.attachPlotEvents = function (chartEl: any) {
  chartEl.on("plotly_click", function (data: any) {
    if (!data || !data.points || data.points.length === 0) return;

    const point = data.points[0];
    const id = point.customdata;

    console.log("Clicked point ID =", id);

    const detail = window.publicOpinionData.find((d: any) => d.id === id);
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

console.log("scatter.js loaded");
