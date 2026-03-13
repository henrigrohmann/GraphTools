// src/scatter.ts

export type ScatterSeries = {
  x: number[]
  y: number[]
  color?: string
  size?: number
  label?: string
}

export function buildScatterData(seriesList: ScatterSeries[]) {
  return seriesList.map((s) => ({
    x: s.x,
    y: s.y,
    mode: "markers",
    type: "scattergl",
    marker: {
      size: s.size ?? 10,
      color: s.color ?? "blue",
    },
    name: s.label ?? "series",
  }))
}

export function buildLayout(title: string) {
  return {
    title,
    hovermode: "closest",
  }
}
