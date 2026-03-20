console.log("[scatter.js] loaded");

const DEFAULT_API_PORT = "8005";

function resolveApiBase() {
    const params = new URLSearchParams(window.location.search);
    const fromQuery = params.get("apiBase");
    if (fromQuery) {
        console.log("[resolveApiBase] Using query param:", fromQuery);
        return fromQuery.replace(/\/$/, "");
    }

    if (window.GRAPHTOOLS_API_BASE) {
        console.log("[resolveApiBase] Using window.GRAPHTOOLS_API_BASE:", window.GRAPHTOOLS_API_BASE);
        return String(window.GRAPHTOOLS_API_BASE).replace(/\/$/, "");
    }

    const origin = window.location.origin;
    console.log("[resolveApiBase] window.location.origin:", origin);
    
    if (!origin || origin === "null") {
        const fallback = `http://127.0.0.1:${DEFAULT_API_PORT}`;
        console.log("[resolveApiBase] origin is null/empty, using fallback:", fallback);
        return fallback;
    }

    if (origin.includes(".app.github.dev")) {
        const result = origin.replace(
            /-\d+\.app\.github\.dev$/,
            `-${DEFAULT_API_PORT}.app.github.dev`
        );
        console.log("[resolveApiBase] Detected Codespaces, rewrote to:", result);
        return result;
    }

    const portMatch = origin.match(/:(\d+)$/);
    if (portMatch) {
        const result = origin.replace(/:(\d+)$/, `:${DEFAULT_API_PORT}`);
        console.log("[resolveApiBase] Rewrote port to", DEFAULT_API_PORT, ":", result);
        return result;
    }

    const fallback = `${origin}:${DEFAULT_API_PORT}`;
    console.log("[resolveApiBase] No port in origin, appending", DEFAULT_API_PORT, ":", fallback);
    return fallback;
}

let CURRENT_API_BASE = resolveApiBase();
console.log("[scatter.js] API_BASE =", CURRENT_API_BASE);

function updateApiBaseLabel() {
    const label = document.getElementById("api-base-label");
    if (label) {
        label.textContent = `API: ${CURRENT_API_BASE}`;
        label.title = "Click to check connection";
    }
}

function buildApiBaseCandidates() {
    const list = [];
    const params = new URLSearchParams(window.location.search);
    const fromQuery = params.get("apiBase");

    if (fromQuery) list.push(fromQuery.replace(/\/$/, ""));
    if (window.GRAPHTOOLS_API_BASE) {
        list.push(String(window.GRAPHTOOLS_API_BASE).replace(/\/$/, ""));
    }

    list.push(CURRENT_API_BASE);

    const origin = window.location.origin;
    if (origin && origin !== "null") {
        if (origin.includes(".app.github.dev")) {
            list.push(origin.replace(/-\d+\.app\.github\.dev$/, "-8005.app.github.dev"));
            list.push(origin.replace(/-\d+\.app\.github\.dev$/, "-8000.app.github.dev"));
        } else {
            list.push(origin.replace(/:(\d+)$/, ":8005"));
            list.push(origin.replace(/:(\d+)$/, ":8000"));
        }
    }

    list.push("http://127.0.0.1:8005");
    list.push("http://localhost:8005");
    list.push("http://127.0.0.1:8000");
    list.push("http://localhost:8000");

    return [...new Set(list.filter(Boolean))];
}

window.addEventListener("DOMContentLoaded", () => {
    updateApiBaseLabel();
    setHealthStatus("Health: 未確認", null);
    log(`===== Initialized =====`);
    log(`API_BASE=${CURRENT_API_BASE}`);
    log(`window.location.origin=${window.location.origin}`);
    log(`window.location.href=${window.location.href}`);
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
    log("=== RUN HEALTH CHECK ===");
    log(`API_BASE(current)=${CURRENT_API_BASE}`);
    setHealthStatus("Health: 確認中...", null);

    const candidates = buildApiBaseCandidates();
    log(`API_BASE candidates=${JSON.stringify(candidates)}`);

    let lastError = null;
    for (const base of candidates) {
        CURRENT_API_BASE = base;
        updateApiBaseLabel();
        try {
            const payload = await fetchJson("/jobs");
            const count = Number.isInteger(payload?.count) ? payload.count : "?";
            log(`✓ HEALTH OK: base=${base} /jobs count=${count}`);
            setHealthStatus(`Health: OK (/jobs count=${count})`, true);
            return;
        } catch (e) {
            lastError = e;
            log(`  candidate NG: ${base} -> ${e.message || e}`);
        }
    }

    log(`✗ HEALTH NG: ${lastError?.message || lastError || "unknown error"}`);
    setHealthStatus("Health: NG", false);
}

async function fetchJson(path) {
    const url = `${CURRENT_API_BASE}${path}`;
    log(`FETCH ${url}`);

    let res;
    try {
        res = await fetch(url, {
            method: "GET",
            headers: { "Accept": "application/json" },
        });
    } catch (e) {
        const err = `Network error: ${e.message || e}`;
        log(`  → ${err}`);
        throw new Error(err);
    }

    log(`  → status ${res.status} ${res.statusText}`);

    let payload = null;
    let bodyText = "";
    try {
        bodyText = await res.text();
        if (bodyText) {
            payload = JSON.parse(bodyText);
        }
    } catch (e) {
        log(`  → JSON parse error: ${e.message}`);
    }

    if (!res.ok) {
        const detail = payload?.detail ? ` detail=${payload.detail}` : "";
        const body = bodyText ? ` body=${bodyText.substring(0, 100)}` : "";
        const err = `HTTP ${res.status} ${res.statusText}${detail}${body}`;
        log(`  → ${err}`);
        throw new Error(err);
    }

    log(`  → OK`);
    return payload;
}

async function runInit() {
    log("=== RUN INIT (pipeline: raw) ===");

    try {
        const json = await fetchJson(`/raw`);
        log(`Init result: ${JSON.stringify(json)}`);

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

    let colors;
    let sizes;
    let top5Indices = [];

    if (mode === "dense") {
        const densities = json.data.map(d => d.density ?? 0);
        const maxD = Math.max(...densities, 1);

        // 色: density に応じて青→赤
        colors = densities.map(d => {
            const t = maxD === 0 ? 0 : d / maxD; // 0〜1
            const r = Math.round(255 * t);
            const g = 50;
            const b = Math.round(255 * (1 - t));
            return `rgb(${r},${g},${b})`;
        });

        // 上位5件の index
        top5Indices = [...densities]
            .map((d, i) => ({ d, i }))
            .sort((a, b) => b.d - a.d)
            .slice(0, 5)
            .map(obj => obj.i);

        // サイズ: density ベース + 上位5件を強調
        sizes = densities.map((d, i) => {
            let s = 6 + d * 10; // 6〜16px
            if (top5Indices.includes(i)) {
                s += 12; // 上位5件はさらに大きく
            }
            return s;
        });
    } else {
        colors = clusters.map(c => {
            if (c === "A") return "red";
            if (c === "B") return "green";
            if (c === "C") return "blue";
            return "gray";
        });
        sizes = xs.map(() => 10);
    }

    // customdata に top5 フラグも載せておく
    const customData = json.data.map((d, idx) => ({
        ...d,
        isTop5Density: top5Indices.includes(idx)
    }));

    const trace = {
        x: xs,
        y: ys,
        mode: "markers",
        type: "scattergl",
        marker: { size: sizes, color: colors },
        text: texts,
        customdata: customData,
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

    const densityText =
        point.density === null || point.density === undefined
            ? "-"
            : point.density.toFixed(3);

    const top5Label = point.isTop5Density ? "（濃度上位5件）" : "";

    panel.innerHTML = `
        <div class="label">ID</div>
        <div class="value">${point.id}</div>

        <div class="label">Cluster</div>
        <div class="value">${point.cluster_id}</div>

        <div class="label">Summary</div>
        <div class="value">${point.summary}</div>

        <div class="label">Full Opinion</div>
        <div class="value">${point.fullOpinion}</div>

        <div class="label">Density</div>
        <div class="value">${densityText} ${top5Label}</div>
    `;
}

async function runDump() {
    try {
        const payload = await fetchJson("/jobs");
        log(`DUMP /jobs: ${JSON.stringify(payload).slice(0, 500)}`);
    } catch (e) {
        log(`DUMP ERROR: ${e.message || e}`);
    }
}

function runFeature(name) {
    log(`Feature '${name}' is not implemented yet.`);
}
