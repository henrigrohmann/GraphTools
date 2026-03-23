# backend/plugins/vectorizer_hash.py
import hashlib

def _h(text: str, salt: str) -> float:
    """salt を混ぜたハッシュ値を 0〜1 に正規化して返す"""
    s = (salt + text).encode("utf-8")
    h = hashlib.md5(s).hexdigest()
    return (int(h, 16) % 10000) / 10000.0

def vectorize_hash(texts):
    """
    texts: [fullOpinion, fullOpinion, ...]
    return: [[v1, v2, ...], ...]  # 6次元ベクトル
    """
    vectors = []
    for t in texts:
        t = t or ""
        v = [
            _h(t, "A"),
            _h(t, "B"),
            _h(t, "C"),
            _h(t, "D"),
            _h(t[: len(t)//2], "E"),
            _h(t[len(t)//2:], "F"),
        ]
        vectors.append(v)
    return vectors
