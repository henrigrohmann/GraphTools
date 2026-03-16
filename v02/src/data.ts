// @ts-nocheck
// data.ts (API wrapper)

window.api = {
  async getDummy() {
    const res = await fetch("http://localhost:8001/dummy");
    return res.json();
  }
};

console.log("data.ts (API wrapper) loaded");
