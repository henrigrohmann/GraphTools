// src/data.ts

export type OpinionPoint = {
  id: string
  text: string
  x: number
  y: number
  cluster: "A" | "B" | "C"
}

// ---- 3つの意見グループを中心に30件生成 ----
// A: 健康被害（左上）
// B: 分煙・ルール（右上）
// C: 喫煙者の権利（中央下）

export const opinions: OpinionPoint[] = [
  // --- Group A (健康被害) ---
  { id: "A1", text: "受動喫煙で頭痛がする", x: -4.2, y: 4.8, cluster: "A" },
  { id: "A2", text: "子どもへの影響が心配", x: -4.5, y: 5.1, cluster: "A" },
  { id: "A3", text: "飲食店は全面禁煙にしてほしい", x: -3.9, y: 4.4, cluster: "A" },
  { id: "A4", text: "煙の匂いが服に残るのが嫌だ", x: -4.1, y: 4.6, cluster: "A" },
  { id: "A5", text: "駅前の喫煙所が近すぎる", x: -4.3, y: 4.9, cluster: "A" },
  { id: "A6", text: "歩きタバコは危険だと思う", x: -3.8, y: 4.7, cluster: "A" },
  { id: "A7", text: "もっと厳しい規制が必要", x: -4.6, y: 4.5, cluster: "A" },
  { id: "A8", text: "禁煙エリアを増やしてほしい", x: -4.0, y: 5.0, cluster: "A" },
  { id: "A9", text: "タバコ税を上げてほしい", x: -4.4, y: 4.3, cluster: "A" },
  { id: "A10", text: "健康保険の負担が心配", x: -3.7, y: 4.8, cluster: "A" },

  // --- Group B (分煙・ルール) ---
  { id: "B1", text: "喫煙所をもっと分かりやすくしてほしい", x: 4.2, y: 4.7, cluster: "B" },
  { id: "B2", text: "分煙が徹底されていれば問題ない", x: 4.5, y: 4.9, cluster: "B" },
  { id: "B3", text: "換気の良い喫煙室を増やしてほしい", x: 4.1, y: 4.4, cluster: "B" },
  { id: "B4", text: "ルールを守らない人が問題", x: 4.3, y: 4.6, cluster: "B" },
  { id: "B5", text: "喫煙所の位置が不便すぎる", x: 4.0, y: 4.8, cluster: "B" },
  { id: "B6", text: "もっと静かな喫煙スペースがほしい", x: 4.6, y: 4.5, cluster: "B" },
  { id: "B7", text: "屋外喫煙所は風向きに配慮してほしい", x: 4.4, y: 4.3, cluster: "B" },
  { id: "B8", text: "喫煙所の混雑をどうにかしてほしい", x: 4.2, y: 5.0, cluster: "B" },
  { id: "B9", text: "分煙のルールをもっと周知してほしい", x: 4.1, y: 4.2, cluster: "B" },
  { id: "B10", text: "喫煙所のマナー向上が必要", x: 4.3, y: 4.1, cluster: "B" },

  // --- Group C (喫煙者の権利) ---
  { id: "C1", text: "喫煙者のスペースが少なすぎる", x: 0.2, y: -4.5, cluster: "C" },
  { id: "C2", text: "吸える場所がほとんどない", x: 0.4, y: -4.7, cluster: "C" },
  { id: "C3", text: "喫煙者ばかりが悪者扱いされている", x: -0.1, y: -4.3, cluster: "C" },
  { id: "C4", text: "もっとバランスの良いルールにしてほしい", x: 0.3, y: -4.6, cluster: "C" },
  { id: "C5", text: "喫煙所を減らしすぎだと思う", x: 0.1, y: -4.8, cluster: "C" },
  { id: "C6", text: "喫煙者の権利も尊重してほしい", x: -0.2, y: -4.4, cluster: "C" },
  { id: "C7", text: "屋外なら自由に吸わせてほしい", x: 0.5, y: -4.2, cluster: "C" },
  { id: "C8", text: "喫煙所の数を元に戻してほしい", x: 0.0, y: -4.9, cluster: "C" },
  { id: "C9", text: "喫煙者への配慮が足りない", x: -0.3, y: -4.6, cluster: "C" },
  { id: "C10", text: "もっと現実的なルールにしてほしい", x: 0.2, y: -4.3, cluster: "C" },
]
