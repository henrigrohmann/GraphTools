# ============================================================
# vectorizer_simple.py — 依存ゼロ・listベース（正史）
# ============================================================

def vectorize(rows):
    """
    rows: (id, summary, fullOpinion, x, y, density)
    → summary + fullOpinion を Bag-of-Words でベクトル化
    → list[list[float]] を返す（k-means と整合）
    """

    # テキスト抽出
    texts = []
    for (_id, summary, fullOpinion, _x, _y, _density) in rows:
        texts.append(f"{summary} {fullOpinion}".strip())

    # 語彙辞書
    vocab = {}
    for text in texts:
        for token in text.split():
            if token not in vocab:
                vocab[token] = len(vocab)

    # ベクトル化（list ベース）
    vectors = []
    for text in texts:
        vec = [0.0] * len(vocab)
        for token in text.split():
            if token in vocab:
                vec[vocab[token]] += 1.0
        vectors.append(vec)

    return vectors
