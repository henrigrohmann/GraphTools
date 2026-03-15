"use strict";
// =======================================
// GraphTool デモ用 data.ts（30点スタブ）
// import/export は使わない
// window.publicOpinionData に公開する
// =======================================
const opinionData = [
    // -------------------------
    // Group A：健康・受動喫煙（Health）
    // -------------------------
    { id: 0, group: "A", category: "Health", opinion: "受動喫煙の影響が心配。公共の場では完全禁煙にしてほしい。" },
    { id: 1, group: "A", category: "Health", opinion: "子どもがいる場所では喫煙を禁止すべきだと思う。" },
    { id: 2, group: "A", category: "Health", opinion: "タバコの煙で頭痛がするので、駅前の喫煙所は改善してほしい。" },
    { id: 3, group: "A", category: "Health", opinion: "飲食店の分煙は不十分。完全禁煙にしてほしい。" },
    { id: 4, group: "A", category: "Health", opinion: "健康被害を考えると、喫煙スペースはもっと隔離すべき。" },
    { id: 5, group: "A", category: "Health", opinion: "歩きタバコは危険なので厳しく取り締まってほしい。" },
    { id: 6, group: "A", category: "Health", opinion: "受動喫煙対策の啓発をもっと強化してほしい。" },
    { id: 7, group: "A", category: "Health", opinion: "公共施設の敷地内禁煙は賛成。もっと広げてほしい。" },
    { id: 8, group: "A", category: "Health", opinion: "タバコの煙が衣服につくのが嫌なので、喫煙所の位置を見直してほしい。" },
    { id: 9, group: "A", category: "Health", opinion: "健康への影響を考えると、喫煙者にはもっと配慮してほしい。" },
    // -------------------------
    // Group B：喫煙場所・ルール（Rules）
    // -------------------------
    { id: 10, group: "B", category: "Rules", opinion: "喫煙所が少なすぎて困る。もっと設置してほしい。" },
    { id: 11, group: "B", category: "Rules", opinion: "屋外の喫煙所は風向きによって煙が流れるので改善が必要。" },
    { id: 12, group: "B", category: "Rules", opinion: "ルールを守らない喫煙者がいるので監視を強化してほしい。" },
    { id: 13, group: "B", category: "Rules", opinion: "喫煙所の案内表示が分かりにくい。もっと明確にしてほしい。" },
    { id: 14, group: "B", category: "Rules", opinion: "駅前の喫煙所は混雑しすぎていて危険。改善が必要。" },
    { id: 15, group: "B", category: "Rules", opinion: "喫煙エリアをもっと広くして、密集を避けられるようにしてほしい。" },
    { id: 16, group: "B", category: "Rules", opinion: "喫煙所の位置が悪く、通行人に煙が流れてしまう。" },
    { id: 17, group: "B", category: "Rules", opinion: "屋内の喫煙室は換気をもっと強化してほしい。" },
    { id: 18, group: "B", category: "Rules", opinion: "喫煙所の利用マナーをもっと周知してほしい。" },
    { id: 19, group: "B", category: "Rules", opinion: "喫煙所の設置基準を統一してほしい。" },
    // -------------------------
    // Group C：喫煙者の権利・配慮（Rights）
    // -------------------------
    { id: 20, group: "C", category: "Rights", opinion: "喫煙者にも配慮して、適切な喫煙スペースを確保してほしい。" },
    { id: 21, group: "C", category: "Rights", opinion: "完全禁煙ばかりではなく、喫煙者の居場所も必要だと思う。" },
    { id: 22, group: "C", category: "Rights", opinion: "喫煙者が肩身の狭い思いをしないようにしてほしい。" },
    { id: 23, group: "C", category: "Rights", opinion: "喫煙所が遠すぎて仕事の合間に利用しづらい。" },
    { id: 24, group: "C", category: "Rights", opinion: "喫煙者への配慮も必要で、バランスの取れたルールが望ましい。" },
    { id: 25, group: "C", category: "Rights", opinion: "喫煙所の数が減りすぎていて不便。" },
    { id: 26, group: "C", category: "Rights", opinion: "喫煙者の権利も尊重されるべきだと思う。" },
    { id: 27, group: "C", category: "Rights", opinion: "喫煙所の環境をもっと快適にしてほしい。" },
    { id: 28, group: "C", category: "Rights", opinion: "喫煙者と非喫煙者が共存できる仕組みが必要。" },
    { id: 29, group: "C", category: "Rights", opinion: "喫煙者が迷惑をかけないようにする仕組みを整えてほしい。" }
];
// window に公開
window.publicOpinionData = opinionData;
