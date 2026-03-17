// @ts-nocheck
console.log("data.js loaded");

// Live Server の URL → 5500
// API の URL → 8001 に自動変換
const API_BASE = window.location.origin.replace("5500", "8001");

window.api = {
  async getScatterData() {
    const url = `${API_BASE}/scatter_data`;
    console.log("FETCH:", url);

    const res = await fetch(url);
    console.log("STATUS:", res.status);

    const json = await res.json();
    console.log("JSON:", json);
    return json;
  }
};
