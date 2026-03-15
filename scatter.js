"use strict";
// =======================================
// GraphTool scatter.ts（data.ts 参照版）
// import/export は使わない
// window.publicOpinionData を利用する
// =======================================
function buildScatterData() {
    // data.ts で公開した 30 点の意見データ
    const raw = window.publicOpinionData;
    const N = raw.length;
    const xs = new Array(N);
    const ys = new Array(N);
    const texts = new Array(N);
    const colors = new Array(N);
    const custom = new Array(N);
    const groupColors = {
        A: "#1e88e5", // 青
        B: "#43a047", // 緑
        C: "#e53935" // 赤
    };
    for (let i = 0; i < N; i++) {
        const item = raw[i];
        // 座標はランダム（本番では UMAP / PCA などに置き換え）
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
    return [
        {
            x: xs,
            y: ys,
            mode: "markers",
            type: "scattergl",
            text: texts,
            customdata: custom,
            marker: {
                size: 12,
                color: colors
            },
            hovertemplate: "<b>ID:</b> %{customdata.id}<br>" +
                "<b>Group:</b> %{customdata.group}<br>" +
                "<b>Category:</b> %{customdata.category}<br>" +
                "<b>Speaker:</b> %{customdata.speaker}<br><br>" +
                "<b>Opinion:</b><br>%{customdata.opinion}<br>" +
                "<extra></extra>"
        }
    ];
}
// レイアウト
function buildLayout() {
    return {
        title: "GraphTool Scatter Demo (30 points)",
        margin: { t: 40 }
    };
}
// =======================================
// クリック → 右パネルに詳細表示
// =======================================
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
                `<b>Category:</b> ${data.category}<br>` +
                `<b>Speaker:</b> ${data.speaker}<br><br>` +
                `<b>Opinion:</b><br>${data.opinion}`;
    });
}
// =======================================
// window に公開（export は使わない）
// =======================================
window.buildScatterData = buildScatterData;
window.buildLayout = buildLayout;
window.attachPlotEvents = attachPlotEvents;
