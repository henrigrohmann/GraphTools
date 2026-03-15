"use strict";
// =======================================
// GraphTool scatter.ts（型警告ゼロ・安定版）
// =======================================
// ---- 画面ログ関数 ----
function log(msg) {
    const el = document.getElementById("bottom-panel");
    if (el)
        el.textContent += "\n" + msg;
}
window.log = log;
log("scatter.js loaded");
// ---- データ生成 ----
function buildScatterData() {
    log("buildScatterData() called");
    // ★ 型エラー回避：window は any 扱い
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
    const groupColors = {
        A: "#1e88e5",
        B: "#43a047",
        C: "#e53935"
    };
    for (let i = 0; i < N; i++) {
        const item = raw[i];
        xs[i] = Math.random() * 10;
        ys[i] = Math.random() * 10;
        texts[i] = `P${item.id}`;
        // ★ 型エラー回避：as で絞る
        colors[i] = groupColors[item.group];
        custom[i] = {
            id: item.id,
            group: item.group,
            category: item.category,
            opinion: item.opinion,
            fullOpinion: item.fullOpinion
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
            hovertemplate: "<b>ID:</b> %{customdata.id}<br>" +
                "<b>Group:</b> %{customdata.group}<br>" +
                "<b>Category:</b> %{customdata.category}<br>" +
                "<b>Opinion:</b> %{customdata.opinion}<br>" +
                "<extra></extra>"
        }
    ];
}
// ---- レイアウト ----
function buildLayout() {
    return {
        title: "GraphTool Scatter Demo (fullOpinion 対応)",
        margin: { t: 40 }
    };
}
// ---- クリックイベント ----
function attachPlotEvents(plotElement) {
    plotElement.on("plotly_click", function (eventData) {
        const point = eventData.points[0];
        const data = point.customdata;
        const panel = document.getElementById("detail-content");
        if (!panel)
            return;
        panel.innerHTML =
            `<b>ID:</b> ${data.id}<br>` +
                `<b>Group:</b> ${data.group}<br>` +
                `<b>Category:</b> ${data.category}<br><br>` +
                `<b>Full Opinion:</b><br>${data.fullOpinion}`;
        log("Clicked point ID = " + data.id);
    });
}
// ---- window に公開 ----
window.buildScatterData = buildScatterData;
window.buildLayout = buildLayout;
window.attachPlotEvents = attachPlotEvents;
