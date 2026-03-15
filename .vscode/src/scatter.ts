import Plotly from "plotly.js-dist-min";
import { publicOpinionData } from "./data";

export function renderScatter() {
  const container = document.getElementById("scatter");
  if (!container) return;

  // x, y, customdata を生成
  const x: number[] = [];
  const y: number[] = [];
  const customdata: any[] = [];

  publicOpinionData.forEach((item) => {
    x.push(item.x);
    y.push(item.y);

    customdata.push([
      item.id,
      item.group,
      item.category,
      item.opinion,
      item.fullOpinion,
      item.meta?.age ?? "",
      item.meta?.gender ?? "",
      item.meta?.region ?? "",
      item.meta?.timestamp ?? "",
      item.meta?.source ?? "",
      item.meta?.tag1 ?? "",
      item.meta?.tag2 ?? "",
      item.meta?.tag3 ?? "",
      item.meta?.tag4 ?? "",
      item.meta?.tag5 ?? "",
      item.meta?.tag6 ?? "",
      item.meta?.tag7 ?? "",
      item.meta?.tag8 ?? "",
      item.meta?.tag9 ?? "",
      item.meta?.tag10 ?? "",
      item.meta?.tag11 ?? "",
      item.meta?.tag12 ?? "",
      item.meta?.tag13 ?? "",
      item.meta?.tag14 ?? "",
      item.meta?.tag15 ?? "",
      item.meta?.tag16 ?? "",
      item.meta?.tag17 ?? "",
      item.meta?.tag18 ?? "",
      item.meta?.tag19 ?? "",
      item.meta?.tag20 ?? "",
    ]);
  });

  const trace = {
    x,
    y,
    mode: "markers",
    type: "scattergl",
    marker: {
      size: 10,
      color: publicOpinionData.map((d) => d.color),
      opacity: 0.9,
    },
    customdata,
    hovertemplate:
      "<b>ID:</b> %{customdata[0]}<br>" +
      "<b>Group:</b> %{customdata[1]}<br>" +
      "<b>Category:</b> %{customdata[2]}<br>" +
      "<b>Opinion:</b> %{customdata[3]}<br>" +
      "<extra></extra>",
  };

  const layout = {
    title: "意見分布図（デモ版）",
    dragmode: "pan",
    hovermode: "closest",
    showlegend: false, // ←←← ★ これだけ追加して凡例を完全に消す
    margin: { l: 40, r: 40, t: 40, b: 40 },
  };

  Plotly.newPlot(container, [trace], layout);

  // クリックイベント → 右パネル更新
  container.on("plotly_click", (event: any) => {
    const point = event.points[0];
    if (!point) return;

    const cd = point.customdata;

    const panel = document.getElementById("detail-panel");
    if (panel) {
      panel.innerHTML = `
        <div class="card">
          <h3>意見詳細</h3>
          <p><b>ID:</b> ${cd[0]}</p>
          <p><b>Group:</b> ${cd[1]}</p>
          <p><b>Category:</b> ${cd[2]}</p>
          <p><b>Opinion:</b> ${cd[3]}</p>
          <p><b>Full Opinion:</b><br>${cd[4]}</p>
        </div>
      `;
    }

    const log = document.getElementById("debug-log");
    if (log) {
      log.innerHTML += `<div>Clicked ID: ${cd[0]}</div>`;
      log.scrollTop = log.scrollHeight;
    }
  });
}
