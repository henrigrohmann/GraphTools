import time

from plugins.loader_csv import load_csv
from plugins.vectorizer_simple import vectorize
from plugins.cluster_kmeans import run_kmeans
from plugins.layout_scatter import assign_xy as assign_cluster_xy
from plugins.layout_random import assign_random_xy
from plugins.writer_db import write_db, read_scatter


def _log_start(logs, name: str):
    logs.append(f"[{time.strftime('%H:%M:%S')}] {name} start")


def _log_end(logs, name: str):
    logs.append(f"[{time.strftime('%H:%M:%S')}] {name} end")


def run_init_pipeline():
    """
    CSV → DB 初期登録。
    ここではクラスタリングも座標生成もせず、
    とりあえず DB に「生データ」を入れておくイメージ。
    （ただし write_db の仕様上、最低限の cluster_id/x/y は入る）
    """
    logs = []
    _log_start(logs, "INIT")

    rows = load_csv()
    logs.append(f"Loaded CSV: {len(rows)} rows")

    # 初期状態ではクラスタリングせず、ランダム座標＋クラスタなしで保存しておく
    labels = [-1] * len(rows)  # -1 = no cluster
    xy = assign_random_xy(len(rows))

    write_db(rows, labels, xy)
    logs.append("DB written (init, no clustering)")

    _log_end(logs, "INIT")
    return logs


def run_raw_pipeline():
    """
    生データ表示用パイプライン。
    - クラスタリングは行わない
    - ランダム座標を振る
    - cluster_id は空（""）として保存
    """
    logs = []
    _log_start(logs, "RAW")

    rows = load_csv()
    logs.append(f"Loaded CSV: {len(rows)} rows")

    labels = [-1] * len(rows)
    xy = assign_random_xy(len(rows))
    logs.append("Random XY assigned")

    write_db(rows, labels, xy)
    logs.append("DB written (raw mode)")

    _log_end(logs, "RAW")
    return logs


def run_cluster_pipeline():
    """
    クラスタリング用パイプライン。
    - summary + fullOpinion をベクトル化
    - なんちゃって k-means で 3 クラスタ
    - クラスタごとに座標を割り当て
    """
    logs = []
    _log_start(logs, "CLUSTER")

    rows = load_csv()
    logs.append(f"Loaded CSV: {len(rows)} rows")

    vectors = vectorize(rows)
    logs.append("Vectorized")

    labels = run_kmeans(vectors, k=3)
    logs.append("Clustered (pseudo k-means)")

    xy = assign_cluster_xy(labels)
    logs.append("Cluster XY assigned")

    write_db(rows, labels, xy)
    logs.append("DB written (cluster mode)")

    _log_end(logs, "CLUSTER")
    return logs


def load_scatter_data():
    """DB → scatter 用データ"""
    return read_scatter()
