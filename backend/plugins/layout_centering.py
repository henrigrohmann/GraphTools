# backend/plugins/layout_centering.py
import random

def assign_xy(cluster_ids, k=3):
    """
    cluster_ids: [0,1,2,0,1,...]
    return: xs, ys
    """

    # クラスタ中心を固定配置（見た目が良い三角形）
    base_centers = {
        0: (-0.6, 0.6),
        1: (0.6, 0.6),
        2: (0.0, -0.6),
    }

    xs, ys = [], []

    for cid in cluster_ids:
        cx, cy = base_centers.get(cid, (0, 0))
        # 少しノイズを足して散らす
        x = cx + random.gauss(0, 0.15)
        y = cy + random.gauss(0, 0.15)
        xs.append(x)
        ys.append(y)

    return xs, ys
