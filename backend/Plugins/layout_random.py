import random


def assign_random_xy(n: int):
    """
    生データ用。クラスタを無視して、
    グラフ全体にランダムに散らばる座標を振る。
    """
    xy = []
    for _ in range(n):
        x = random.uniform(-1.0, 1.0)
        y = random.uniform(-1.0, 1.0)
        xy.append((x, y))
    return xy
