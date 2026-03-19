console.log("[scatter.js] loaded");

const DEFAULT_API_PORT = "8000";

function resolveApiBase() {
    const params = new URLSearchParams(window.location.search);
    const fromQuery = params.get("apiBase");
    if (fromQuery) {
        return fromQuery.replace(/\/$/, "");
    }

    if (window.GRAPHTOOLS_API_BASE) {
        return String(window.GRAPHTOOLS_API_BASE).replace(/\/$/, "");
    }

    const origin = window.location.origin;
    if (!origin || origin === "null") {
        return `http://127.0.0.1:${DEFAULT_API_PORT}`;
    }

    if (origin.includes(".app.github.dev")) {
        return origin.replace(
            /-\d+\.app\.github\.dev$/,
            `-${DEFAULT_API_PORT}.app.github.dev`
        );
    }

    const portMatch = origin.match(/:(\d+)$/);
    if (portMatch) {
        return origin.replace(/:(\d+)$/, `:${DEFAULT_API_PORT}`);
    }

    return `${origin}:${DEFAULT_API_PORT}`;
}

const API_BASE = resolveApiBase();
console.log("[scatter.js] API_BASE =", API_BASE);

window.addEventListener("DOMContentLoaded", () => {
    const label = document.getElementById("api-base-label");
    if (label) {
        label.textContent = `API: ${API_BASE}`;
    }
    setHealthStatus("Health: 未確認", null);
    log(`API_BASE=${API_BASE}`);
});

function log(msg) {
    const panel = document.getElementById("bottom-panel");
    panel.textContent += `[${new Date().toLocaleTimeString()}] ${msg}\n`;
    panel.scrollTop = panel.scrollHeight;
}

function setHealthStatus(text, ok) {
    const el = document.getElementById("health-status");
    if (!el) return;

    el.textContent = text;
    if (ok === true) {
        el.style.color = "#0a7a0a";
    } else if (ok === false) {
        el.style.color = "#b00020";
    } else {
        el.style.color = "#666";
    }
}

async function runHealthCheck() {
    log("RUN HEALTH CHECK");
    setHealthStatus("Health: 確認中...", null);

    try {
        const payload = await fetchJson("/jobs");
        const count = Number.isInteger(payload?.count) ? payload.count : "?";
        log(`HEALTH OK: /jobs count=${count}`);
        setHealthStatus(`Health: OK (/jobs count=${count})`, true);
    } catch (e) {
        log(`HEALTH NG: ${e}`);
        setHealthStatus(`Health: NG (${e})`, false);
    }
}

async function fetchJson(path) {
    const url = `${API_BASE}${path}`;
    log(`FETCH ${url}`);

    let res;
    try {
        res = await fetch(url);
    } catch (e) {
        throw new Error(`Network error: ${e}`);
    }

    let payload = null;
    try {
        payload = await res.json();
    } catch (_e) {
        // JSON が返らない場合は payload を null のまま扱う
    }

    if (!res.ok) {
        const detail = payload?.detail ? ` detail=${payload.detail}` : "";
        throw new Error(`HTTP ${res.status} ${res.statusText}${detail}`);
    }

    return payload;
}

async function runInit() {
    log("RUN INIT (raw pipeline)");

    try {
        const json = await fetchJson(`/raw`);
        log(`Init result: ${JSON.stringify(json)}`);

        // 初期化後は RAW を読み込む
        await loadScatter("raw");
    } catch (e) {
        log(`ERROR: ${e}`);
    }
}

async function runPipeline(mode) {
    log(`RUN PIPELINE: ${mode}`);

    try {
        const json = await fetchJson(`/${mode}`);
        log(`Pipeline result: ${JSON.stringify(json)}`);

        await loadScatter(mode);
    } catch (e) {
        log(`ERROR: ${e}`);
    }
}

async function loadScatter(mode) {
    log(`LOAD SCATTER: ${mode}`);

    let json;
    try {
        json = await fetchJson(`/scatter?mode=${encodeURIComponent(mode)}`);
    } catch (e) {
        log(`ERROR: ${e}`);
        return;
    }

    if (!json || !Array.isArray(json.data)) {
        log(`ERROR: Invalid scatter payload: ${JSON.stringify(json)}`);
        return;
    }

    const xs = json.data.map(d => d.x);
    const ys = json.data.map(d => d.y);
    const clusters = json.data.map(d => d.cluster_id);
    const texts = json.data.map(d => d.summary);

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
    plotDiv.removeAllListeners?.("plotly_click");

    plotDiv.on("plotly_click", (event) => {
        const point = event.points[0].customdata;
        updateRightPanel(point);
    });

    log(`SCATTER READY: mode=${mode}, count=${json.count ?? json.data.length}`);
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
