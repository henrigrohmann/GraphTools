import random


def assign_random_xy(n: int):
    """
    n 個の点に対してランダム座標を生成する。
    -1.0 ～ +1.0 の範囲に均等に散らす。
    """
    result = []
    for _ in range(n):
        x = random.uniform(-1.0, 1.0)
        y = random.uniform(-1.0, 1.0)
        result.append((x, y))
    return result
