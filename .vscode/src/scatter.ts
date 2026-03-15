// =======================================
// GraphTool scatter.ts（ログ付き / 型警告ゼロ版）
// =======================================

// ---- window の型を拡張（警告ゼロのための重要ポイント）----
declare global {
  interface Window {
    publicOpinionData: Array<{
      id: number;
      group: "A" | "B" | "C";
      category: string;
      opinion: string;
    }>;
    log: (msg: string) => void;
    _pendingLog?: string;
  }
}

// ---- 画面ログ関数（msg: string）----
function log(msg: string) {
  const el = document.getElementById("debug-log");
  if (el) el.textContent += "\n" + msg;
}
window.log = log;

// ---- データ生成 ----
function buildScatterData() {
  log("buildScatterData() called");

  const raw = window.publicOpinionData;
  log("publicOpinionData = " + (raw ? "OK (" + raw.length + " items)" : "undefined"));

  if (!raw) {
    log("ERROR: publicOpinionData is undefined");
    return [];
  }

  const N = raw.length;
  const xs = new Array(N);
  const ys = new Array(N);
  const texts = new Array(N);
  const colors = new Array(N);
  const custom = new Array(N);

  const groupColors: Record<string, string> = {
    A: "#1e88e5",
    B: "#43a047",
    C: "#e53935"
  };

  for (let i = 0; i < N; i++) {
    const item = raw[i];

    xs[i] = Math.random() * 10;
    ys[i] = Math.random() * 10;

    texts[i] = `P${item.id}`;
    colors[i] = groupColors[item.group];

    custom[i] = {
      id: item.id,
      group: item.group,
      category: item.category,
      speaker: `Speaker ${item.id}`,
      opinion: item.opinion
    };
  }

  log("Scatter data generated.");

  return [
    {
      x: xs,
      y: ys,
      mode: "markers",
      type: "scattergl",
      text: texts,
      customdata: custom,
      marker: { size: 12, color: colors },
      hovertemplate:
        "<b>ID:</b> %{customdata.id}<br>" +
        "<b>Group:</b> %{customdata.group}<br>" +
        "<b>Category:</b> %{customdata.category}<br>" +
        "<b>Speaker:</b> %{customdata.speaker}<br><br>" +
        "<b>Opinion:</b><br>%{customdata.opinion}<br>" +
        "<extra></extra>"
    }
  ];
}

// ---- レイアウト ----
function buildLayout() {
  return {
    title: "GraphTool Scatter Demo (30 points)",
    margin: { t: 40 }
  };
}

// ---- クリックイベント ----
function attachPlotEvents(plotElement: any) {
  plotElement.on("plotly_click", function (eventData: any) {
    const point = eventData.points[0];
    const data = point.customdata;

    const panel = document.getElementById("detail-content");
    if (!panel) return;

    panel.innerHTML =
      `<b>ID:</b> ${data.id}<br>` +
      `<b>Group:</b> ${data.group}<br>` +
      `<b>Category:</b> ${data.category}<br>` +
      `<b>Speaker:</b> ${data.speaker}<br><br>` +
      `<b>Opinion:</b><br>${data.opinion}`;

    log("Clicked point ID = " + data.id);
  });
}

// ---- window に公開 ----
window.buildScatterData = buildScatterData;
window.buildLayout = buildLayout;
window.attachPlotEvents = attachPlotEvents;
