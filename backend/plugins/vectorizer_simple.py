import re
import math


def _tokenize(text: str) -> list[str]:
    """
    超簡易トークナイザ。
    - 記号をスペースに置換
    - 全角・半角を問わず日本語も英語もそのまま分割
    """
    text = re.sub(r"[^\wぁ-んァ-ン一-龥]", " ", text)
    tokens = text.split()
    return tokens


def vectorize(rows):
    """
    rows: [(id, summary, fullOpinion, x, y), ...]
    summary + fullOpinion を連結して簡易ベクトル化する。

    出力:
        vectors: [[float, float, ...], ...]
    """
    docs = []
    for (_id, summary, fullOpinion, _x, _y) in rows:
        text = f"{summary} {fullOpinion}"
        docs.append(_tokenize(text))

    # 語彙を作る
    vocab = {}
    for tokens in docs:
        for t in tokens:
            if t not in vocab:
                vocab[t] = len(vocab)

    # Bag-of-Words ベクトル化
    vectors = []
    for tokens in docs:
        vec = [0] * len(vocab)
        for t in tokens:
            idx = vocab[t]
            vec[idx] += 1
        vectors.append(vec)

    # 正規化（L2）
    normed = []
    for vec in vectors:
        s = math.sqrt(sum(v * v for v in vec))
        if s == 0:
            normed.append(vec)
        else:
            normed.append([v / s for v in vec])

    return normed