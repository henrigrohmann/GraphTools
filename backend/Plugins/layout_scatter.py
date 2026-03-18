import random


def assign_xy(labels):
    """
    クラスタラベルごとに、だいたい近傍に集まるような座標を振る。
    0 → 左上、1 → 右上、2 → 下側、というイメージ。
    """
    xy = []
    for label in labels:
        if label == 0:
            base_x, base_y = -0.5, 0.5
        elif label == 1:
            base_x, base_y = 0.5, 0.5
        else:
            base_x, base_y = 0.0, -0.5

        x = base_x + random.uniform(-0.2, 0.2)
        y = base_y + random.uniform(-0.2, 0.2)
        xy.append((x, y))
    return xy
