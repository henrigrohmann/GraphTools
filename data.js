// @ts-nocheck
console.log("data.js loaded");

window.api = {
  async getScatterData() {
    const res = await fetch("http://localhost:8001/scatter_data");
    return res.json();
  }
};
