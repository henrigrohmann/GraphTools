# ============================================================
# vectorizer_simple.py — 6要素対応版（正史）
# ============================================================

import numpy as np

def vectorize(rows):
    """
    rows: (id, summary, fullOpinion, x, y, density)
    → summary + fullOpinion を単純 Bag-of-Words ベクトル化
    """

    texts = []
    for (_id, summary, fullOpinion, _x, _y, _density) in rows:
        text = f"{summary} {fullOpinion}".strip()
        texts.append(text)

    # 単純な語彙辞書
    vocab = {}
    for text in texts:
        for token in text.split():
            if token not in vocab:
                vocab[token] = len(vocab)

    # ベクトル化
    vectors = np.zeros((len(texts), len(vocab)), dtype=float)

    for i, text in enumerate(texts):
        for token in text.split():
            if token in vocab:
                vectors[i][vocab[token]] += 1.0

    return vectors
