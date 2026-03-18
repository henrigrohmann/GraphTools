import random


def assign_xy(labels):
    """
    クラスタリング結果 labels（0,1,2,...）に基づいて
    クラスタごとに座標を重心周りに寄せる。

    3 クラスタ想定（A,B,C）だが、labels の値に応じて自動配置。
    """

    n = len(labels)
    if n == 0:
        return []

    # クラスタごとの中心（デモ用に固定配置）
    # A: 左上, B: 右上, C: 下
    centers = {
        0: (-0.6, 0.6),
        1: (0.6, 0.6),
        2: (0.0, -0.6),
    }

    result = []
    for label in labels:
        cx, cy = centers.get(label % 3, (0.0, 0.0))

        # クラスタ中心の周りに少し散らす
        x = random.gauss(cx, 0.15)
        y = random.gauss(cy, 0.15)

        result.append((x, y))

    return result
