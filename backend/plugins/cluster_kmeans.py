# ============================================================
# cluster_kmeans.py — 依存ゼロ・軽量 k-means（正史版）
# ============================================================

import random
import math


def _distance(a, b):
    """2点間のユークリッド距離"""
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def run_kmeans(vectors, k=3, max_iter=10):
    """
    超軽量 k-means（依存ゼロ）
    vectors: [[float, float, ...], ...]  ← list ベース前提
    出力: labels = [0,1,2,...]
    """

    n = len(vectors)
    if n == 0:
        return []

    # 初期中心をランダムに選ぶ
    centers = random.sample(vectors, k)
    labels = [0] * n

    for _ in range(max_iter):

        # --- 各点を最も近い中心に割り当て ---
        for i, v in enumerate(vectors):
            dists = [_distance(v, c) for c in centers]
            labels[i] = dists.index(min(dists))

        # --- 新しい中心を計算 ---
        new_centers = []
        for ci in range(k):
            members = [vectors[i] for i in range(n) if labels[i] == ci]

            if not members:
                # メンバーがいないクラスタはランダム再配置
                new_centers.append(random.choice(vectors))
                continue

            dim = len(vectors[0])
            mean = [0.0] * dim

            for v in members:
                for d in range(dim):
                    mean[d] += v[d]

            mean = [x / len(members) for x in mean]
            new_centers.append(mean)

        # --- 収束チェック ---
        if all(_distance(a, b) < 1e-6 for a, b in zip(centers, new_centers)):
            break

        centers = new_centers

    return labels
