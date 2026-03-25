# ============================================================
# cluster_kmeans.py — 正史版（numpy対応）
# ============================================================

import random
import numpy as np
from sklearn.cluster import KMeans

def run_kmeans(vectors, k=3):
    """
    vectors: numpy.ndarray
    → k-means クラスタリングしてラベルを返す
    """

    # numpy 配列を list に変換して random.sample に渡す
    centers = random.sample(list(vectors), k)

    model = KMeans(n_clusters=k, init=np.array(centers), n_init=1)
    model.fit(vectors)

    return model.labels_
