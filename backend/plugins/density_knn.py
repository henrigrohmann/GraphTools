# plugins/density_knn.py
import math

def _distance(a, b):
    """6次元ベクトル間のユークリッド距離"""
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5

def compute_density(vecs, k=5):
    """
    vecs: [[float, float, ...], ...]  # vectorizer の出力（6次元）
    return: 正規化された密度値リスト（0〜1）
    """
    n = len(vecs)
    if n == 0:
        return []

    densities = []
    for i, v in enumerate(vecs):
        dists = sorted(
            _distance(v, vecs[j])
            for j in range(n) if j != i
        )
        # 近いほど密度が高い → 逆数
        density = 1.0 / (1e-6 + sum(dists[:k]) / k)
        densities.append(density)

    # 正規化（0〜1）
    mn, mx = min(densities), max(densities)
    return [(d - mn) / (mx - mn + 1e-6) for d in densities]
