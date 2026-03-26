function api() {
  return document.getElementById("apiBase").value;
}

function log(msg) {
  const el = document.getElementById("log");
  el.textContent += `[${new Date().toLocaleTimeString()}] ${msg}\n`;
  el.scrollTop = el.scrollHeight;
}

function addResult(test, ok, ms, detail) {
  const row = document.createElement("tr");
  row.innerHTML = `
    <td>${test}</td>
    <td>${ok ? "OK" : "FAIL"}</td>
    <td>${ms}</td>
    <td><pre>${JSON.stringify(detail, null, 2)}</pre></td>
  `;
  document.getElementById("resultTable").appendChild(row);
}

async function runTest(name, fn) {
  const t0 = performance.now();
  try {
    const json = await fn();
    const t1 = performance.now();
    addResult(name, true, Math.round(t1 - t0), json);
  } catch (e) {
    const t1 = performance.now();
    addResult(name, false, Math.round(t1 - t0), { error: e.toString() });
  }
}

async function runInit() {
  return runTest("Init", async () => {
    const url = api() + "/init";
    log("FETCH " + url);
    const res = await fetch(url, { method: "POST" });
    return await res.json();
  });
}

async function runScatterRaw() {
  return runTest("Scatter (raw)", async () => {
    const url = api() + "/scatter?mode=raw";
    log("FETCH " + url);
    const res = await fetch(url);
    return await res.json();
  });
}

async function runScatterCluster() {
  return runTest("Scatter (cluster)", async () => {
    const url = api() + "/scatter?mode=cluster";
    log("FETCH " + url);
    const res = await fetch(url);
    return await res.json();
  });
}

async function runScatterDense() {
  return runTest("Scatter (dense)", async () => {
    const url = api() + "/scatter?mode=dense";
    log("FETCH " + url);
    const res = await fetch(url);
    return await res.json();
  });
}

async function runHierarchyCluster() {
  return runTest("Hierarchy (cluster)", async () => {
    const url = api() + "/hierarchy?mode=cluster";
    log("FETCH " + url);
    const res = await fetch(url);
    return await res.json();
  });
}

async function runDump() {
  return runTest("Dump", async () => {
    const url = api() + "/dump";
    log("FETCH " + url);
    const res = await fetch(url);
    return await res.json();
  });
}

async function runHealth() {
  return runTest("Health", async () => {
    const url = api() + "/health";
    log("FETCH " + url);
    const res = await fetch(url);
    return await res.json();
  });
}
