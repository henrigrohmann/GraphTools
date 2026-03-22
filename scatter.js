// ===============================
//  API Base 自動検出
// ===============================
let API_BASE = "";

function detectApiBase() {
  const url = window.location.href;

  // Codespaces
  if (url.includes(".app.github.dev")) {
    const m = url.match(/https:\/\/(.+)-8002\.app\.github\.dev/);
    if (m) {
      API_BASE = `https://${m[1]}-8005.app.github.dev`;
    }
  }

  // ローカル
  if (!API_BASE) {
    API_BASE = "http://localhost:8005";
  }

  document.getElementById("api-base-text").textContent = API_BASE;
}

// ===============================
//  ログ出力
// ===============================
function logMessage(msg) {
  const panel = document.getElementById("log-panel");
  panel.textContent += msg + "\n";
  panel.scrollTop = panel.scrollHeight;
}

// ===============================
//  汎用 fetch
// ===============================
async function fetchJson(path) {
  const url = API_BASE + path;
  logMessage(`GET ${url}`);

  try {
    const res = await fetch(url);
    const data = await res.json();
    logMessage(JSON.stringify(data, null, 2));
    return data;
  } catch (e) {
    logMessage("ERROR: " + e);
    return null;
  }
}

// ===============================
//  散布図ロード
// ===============================
async function loadScatter(mode) {
  updateBreadcrumb(`散布図 / ${mode}`);

  const data = await fetchJson(`/scatter?mode=${mode}`);
  if (!data) return;

  const trace = {
    x: data.map(p => p.x),
    y: data.map(p => p.y),
    text: data.map(p => p.summary),
    mode: "markers",
    type: "scatter",
    marker: {
      color: data.map(p => p.color || "#1f77b4"),
      size: data.map(p => p.size || 8)
    }
  };

  const layout = {
    margin: { t: 20, r: 20, b: 40, l: 40 }
  };

  Plotly.newPlot("plot", [trace], layout);

  // 点クリックイベント
  const plotDiv = document.getElementById("plot");
  plotDiv.on("plotly_click", ev => {
    const idx = ev.points[0].pointIndex;
    showDetail(data[idx]);
  });
}

// ===============================
//  詳細表示
// ===============================
function showDetail(point) {
  updateBreadcrumb(`散布図 / 詳細 / ${point.id}`);

  const div = document.getElementById("detail-content");
  div.innerHTML = `
    <h3>ID: ${point.id}</h3>
    <p><b>summary:</b><br>${point.summary}</p>
    <p><b>fullOpinion:</b><br>${point.fullOpinion}</p>
  `;
}

// ===============================
//  階層ビュー
// ===============================
async function loadHierarchy() {
  updateBreadcrumb("階層ビュー");

  const data = await fetchJson("/hierarchy?mode=cluster");
  if (!data) return;

  renderHierarchy(data);
}

function renderHierarchy(h) {
  const div = document.getElementById("hierarchy-content");
  div.innerHTML = "";

  // clusterList
  if (h.clusterList) {
    const h3 = document.createElement("h3");
    h3.textContent = "Clusters";
    div.appendChild(h3);

    h.clusterList.forEach(c => {
      const d = document.createElement("div");
      d.style.marginBottom = "8px";
      d.innerHTML = `
        <b>${c.clusterId}</b><br>
        members: ${c.memberIds.length}
      `;
      div.appendChild(d);
    });
  }

  // argumentList
  if (h.argumentList) {
    const h3 = document.createElement("h3");
    h3.textContent = "Arguments";
    div.appendChild(h3);

    h.argumentList.forEach(a => {
      const d = document.createElement("div");
      d.style.marginBottom = "8px";
      d.innerHTML = `
        <b>${a.argumentId}</b><br>
        members: ${a.memberIds.length}
      `;
      div.appendChild(d);
    });
  }
}

// ===============================
//  パンくず
// ===============================
function updateBreadcrumb(text) {
  document.getElementById("breadcrumb").textContent = text;
}

// ===============================
//  タブ切り替え
// ===============================
function setupTabs() {
  const tabs = document.querySelectorAll(".tab-btn");
  tabs.forEach(btn => {
    btn.addEventListener("click", () => {
      tabs.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");

      const tab = btn.dataset.tab;
      document.querySelectorAll(".tab-content").forEach(c => {
        c.classList.remove("active");
      });
      document.getElementById(`tab-${tab}`).classList.add("active");

      if (tab === "hierarchy") {
        loadHierarchy();
      }
    });
  });
}

// ===============================
//  初期化
// ===============================
window.addEventListener("DOMContentLoaded", () => {
  detectApiBase();
  setupTabs();
  updateBreadcrumb("準備完了");
});
