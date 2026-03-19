console.log("[scatter.js] loaded");

const API_BASE = window.location.origin;

async function runPipeline(mode) {
    console.log(`---- RUN PIPELINE: ${mode} ----`);

    try {
        const res = await fetch(`${API_BASE}/${mode}`);
        const json = await res.json();
        console.log("Pipeline result:", json);

        await loadScatter(mode);
    } catch (e) {
        console.error("ERROR:", e);
    }
}

async function loadScatter(mode) {
    console.log(`---- LOAD SCATTER: ${mode} ----`);

    const res = await fetch(`${API_BASE}/scatter?mode=${mode}`);
    const json = await res.json();

    const xs = json.data.map(d => d.x);
    const ys = json.data.map(d => d.y);
    const texts = json.data.map(d => d.summary);
    const clusters = json.data.map(d => d.cluster_id);

    const colors = clusters.map(c => {
        if (c === "A") return "red";
        if (c === "B") return "green";
        if (c === "C") return "blue";
        return "gray";
    });

    const trace = {
        x: xs,
        y: ys,
        mode: "markers",
        type: "scattergl",
        marker: { size: 10, color: colors },
        text: texts,
        customdata: json.data,
    };

    Plotly.newPlot("plot", [trace], {
        margin: { t: 20, r: 20, l: 20, b: 20 }
    });

    const plotDiv = document.getElementById("plot");

    plotDiv.on("plotly_click", (event) => {
        const point = event.points[0].customdata;
        updateRightPanel(point);
    });
}

function updateRightPanel(point) {
    const panel = document.getElementById("detail-content");

    panel.innerHTML = `
        <div class="label">ID</div>
        <div class="value">${point.id}</div>

        <div class="label">Cluster</div>
        <div class="value">${point.cluster_id}</div>

        <div class="label">Summary</div>
        <div class="value">${point.summary}</div>

        <div class="label">Full Opinion</div>
        <div class="value">${point.fullOpinion}</div>
    `;
}
