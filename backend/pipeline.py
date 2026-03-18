import time
import uuid
from datetime import datetime

from plugins.loader_csv import load_csv
from plugins.vectorizer_simple import vectorize
from plugins.cluster_kmeans import run_kmeans
from plugins.layout_random import assign_random_xy
from plugins.layout_scatter import assign_xy as assign_cluster_xy

from writer_db import (
    write_opinions,
    log_job,
    TABLE_OPINIONS_RAW,
    TABLE_OPINIONS_RANDOM,
    TABLE_OPINIONS_CLUSTERED,
)


def _now_iso():
    return datetime.utcnow().isoformat(timespec="seconds")


def _start_job(pipeline_name: str) -> dict:
    """
    JOB ログの初期化。
    """
    job_id = f"{pipeline_name}-{_now_iso().replace(':','').replace('-','')}-{uuid.uuid4().hex[:6]}"

    return {
        "pipeline": pipeline_name,
        "mode": "sync",          # 将来 async に拡張可能
        "status": "running",
        "started_at": _now_iso(),
        "finished_at": None,
        "duration_ms": None,
        "steps": [],
        "error": None,
        "job_id": job_id,
        "timeout_ms": 30000      # 将来の async タイムアウト管理用
    }


def _finish_job(job: dict, status: str, error: str | None = None):
    """
    JOB ログの終了処理。
    """
    job["status"] = status
    job["finished_at"] = _now_iso()

    # duration
    try:
        t0 = datetime.fromisoformat(job["started_at"])
        t1 = datetime.fromisoformat(job["finished_at"])
        job["duration_ms"] = int((t1 - t0).total_seconds() * 1000)
    except Exception:
        job["duration_ms"] = None

    if error:
        job["error"] = error

    # DB に保存
    log_job(job, is_debug=True)


# ============================================================
#  RAW PIPELINE
# ============================================================

def run_raw_pipeline():
    """
    CSV → 座標そのまま or ランダム → opinions_raw に保存
    """
    job = _start_job("raw")
    try:
        job["steps"].append("load_csv")
        rows = load_csv()

        payloads = []
        for (id_, summary, fullOpinion, x, y) in rows:
            # CSV に座標があればそのまま、無ければランダム
            if x is None or y is None:
                job["steps"].append("assign_random_xy")
                rx, ry = assign_random_xy(1)[0]
            else:
                rx, ry = x, y

            payloads.append({
                "id": id_,
                "cluster_id": "",
                "x": rx,
                "y": ry,
                "summary": summary,
                "fullOpinion": fullOpinion
            })

        job["steps"].append("write_db")
        write_opinions(TABLE_OPINIONS_RAW, payloads)

        _finish_job(job, "success")
        return {"status": "ok", "count": len(payloads)}

    except Exception as e:
        _finish_job(job, "error", str(e))
        raise


# ============================================================
#  RANDOM PIPELINE
# ============================================================

def run_random_pipeline():
    """
    CSV → 座標無視してランダム → opinions_random に保存
    """
    job = _start_job("random")
    try:
        job["steps"].append("load_csv")
        rows = load_csv()

        job["steps"].append("assign_random_xy")
        xy = assign_random_xy(len(rows))

        payloads = []
        for (row, (rx, ry)) in zip(rows, xy):
            id_, summary, fullOpinion, _x, _y = row
            payloads.append({
                "id": id_,
                "cluster_id": "",
                "x": rx,
                "y": ry,
                "summary": summary,
                "fullOpinion": fullOpinion
            })

        job["steps"].append("write_db")
        write_opinions(TABLE_OPINIONS_RANDOM, payloads)

        _finish_job(job, "success")
        return {"status": "ok", "count": len(payloads)}

    except Exception as e:
        _finish_job(job, "error", str(e))
        raise


# ============================================================
#  CLUSTER PIPELINE
# ============================================================

def run_cluster_pipeline():
    """
    CSV → ベクトル化 → k-means → 座標生成 → opinions_clustered に保存
    """
    job = _start_job("cluster")
    try:
        job["steps"].append("load_csv")
        rows = load_csv()

        job["steps"].append("vectorize")
        vectors = vectorize(rows)

        job["steps"].append("kmeans")
        labels = run_kmeans(vectors, k=3)

        job["steps"].append("assign_cluster_xy")
        xy = assign_cluster_xy(labels)

        payloads = []
        for (row, label, (rx, ry)) in zip(rows, labels, xy):
            id_, summary, fullOpinion, _x, _y = row
            cluster_name = ["A", "B", "C"][label % 3]

            payloads.append({
                "id": id_,
                "cluster_id": cluster_name,
                "x": rx,
                "y": ry,
                "summary": summary,
                "fullOpinion": fullOpinion
            })

        job["steps"].append("write_db")
        write_opinions(TABLE_OPINIONS_CLUSTERED, payloads)

        _finish_job(job, "success")
        return {"status": "ok", "count": len(payloads)}

    except Exception as e:
        _finish_job(job, "error", str(e))
        raise
