import uuid
from datetime import datetime

try:
    from .plugins.loader_csv import load_csv
    from .plugins.vectorizer_simple import vectorize
    from .plugins.cluster_kmeans import run_kmeans
    from .plugins.layout_random import assign_random_xy
    from .plugins.layout_scatter import assign_xy as assign_cluster_xy
    from .plugins.density_knn import compute_density  # ★ 追加

    from .plugins.writer_db import (
        write_opinions,
        log_job,
        TABLE_OPINIONS_RAW,
        TABLE_OPINIONS_RANDOM,
        TABLE_OPINIONS_CLUSTERED,
        TABLE_OPINIONS_DENSE,  # ★ 追加
    )
except ImportError:
    # Fallback for direct execution from backend directory.
    from plugins.loader_csv import load_csv
    from plugins.vectorizer_simple import vectorize
    from plugins.cluster_kmeans import run_kmeans
    from plugins.layout_random import assign_random_xy
    from plugins.layout_scatter import assign_xy as assign_cluster_xy
    from plugins.density_knn import compute_density  # ★ 追加

    from plugins.writer_db import (
        write_opinions,
        log_job,
        TABLE_OPINIONS_RAW,
        TABLE_OPINIONS_RANDOM,
        TABLE_OPINIONS_CLUSTERED,
        TABLE_OPINIONS_DENSE,  # ★ 追加
    )


def _now_iso():
    return datetime.utcnow().isoformat(timespec="seconds")


def _start_job(pipeline_name: str) -> dict:
    job_id = f"{pipeline_name}-{_now_iso().replace(':','').replace('-','')}-{uuid.uuid4().hex[:6]}"
    return {
        "pipeline": pipeline_name,
        "mode": "sync",
        "status": "running",
        "started_at": _now_iso(),
        "finished_at": None,
        "duration_ms": None,
        "steps": [],
        "error": None,
        "job_id": job_id,
        "timeout_ms": 30000,
    }


def _finish_job(job: dict, status: str, error: str | None = None):
    job["status"] = status
    job["finished_at"] = _now_iso()

    try:
        t0 = datetime.fromisoformat(job["started_at"])
        t1 = datetime.fromisoformat(job["finished_at"])
        job["duration_ms"] = int((t1 - t0).total_seconds() * 1000)
    except Exception:
        job["duration_ms"] = None

    if error:
        job["error"] = error

    log_job(job)


# ============================================================
#  RAW PIPELINE
# ============================================================

def run_raw_pipeline(csv_path: str | None = None):
    """
    CSV → 座標そのまま or ランダム → opinions_raw に保存
    csv_path が指定されていればその CSV を読む。
    """
    job = _start_job("raw")
    try:
        job["steps"].append("load_csv")
        rows = load_csv(csv_path)

        payloads = []
        for (id_, summary, fullOpinion, x, y, _density) in rows:
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
                "fullOpinion": fullOpinion,
                "density": None,
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

def run_random_pipeline(csv_path: str | None = None):
    """
    CSV → 座標無視してランダム → opinions_random に保存
    """
    job = _start_job("random")
    try:
        job["steps"].append("load_csv")
        rows = load_csv(csv_path)

        job["steps"].append("assign_random_xy")
        xy = assign_random_xy(len(rows))

        payloads = []
        for (row, (rx, ry)) in zip(rows, xy):
            id_, summary, fullOpinion, _x, _y, _density = row
            payloads.append({
                "id": id_,
                "cluster_id": "",
                "x": rx,
                "y": ry,
                "summary": summary,
                "fullOpinion": fullOpinion,
                "density": None,
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

def run_cluster_pipeline(csv_path: str | None = None):
    """
    CSV → ベクトル化 → k-means → 座標生成 → opinions_clustered に保存
    """
    job = _start_job("cluster")
    try:
        job["steps"].append("load_csv")
        rows = load_csv(csv_path)

        job["steps"].append("vectorize")
        vectors = vectorize(rows)

        job["steps"].append("kmeans")
        labels = run_kmeans(vectors, k=3)

        job["steps"].append("assign_cluster_xy")
        xy = assign_cluster_xy(labels)

        payloads = []
        for (row, label, (rx, ry)) in zip(rows, labels, xy):
            id_, summary, fullOpinion, _x, _y, _density = row
            cluster_name = ["A", "B", "C"][label % 3]

            payloads.append({
                "id": id_,
                "cluster_id": cluster_name,
                "x": rx,
                "y": ry,
                "summary": summary,
                "fullOpinion": fullOpinion,
                "density": None,
            })

        job["steps"].append("write_db")
        write_opinions(TABLE_OPINIONS_CLUSTERED, payloads)

        _finish_job(job, "success")
        return {"status": "ok", "count": len(payloads)}

    except Exception as e:
        _finish_job(job, "error", str(e))
        raise


# ============================================================
#  DENSE PIPELINE（新規）
# ============================================================

def run_dense_pipeline(csv_path: str | None = None):
    """
    CSV → ベクトル化 → 密度計算 → 上位20%抽出 → 座標生成 → opinions_dense に保存
    """
    job = _start_job("dense")
    try:
        job["steps"].append("load_csv")
        rows = load_csv(csv_path)

        if not rows:
            _finish_job(job, "success")
            return {"status": "ok", "count": 0}

        job["steps"].append("vectorize")
        vectors = vectorize(rows)

        job["steps"].append("compute_density")
        dens_norm = compute_density(vectors, k=5)

        job["steps"].append("select_top")
        sorted_d = sorted(dens_norm)
        threshold = sorted_d[int(len(sorted_d) * 0.8)] if len(sorted_d) > 1 else sorted_d[0]
        dense_indices = [i for i, d in enumerate(dens_norm) if d >= threshold]

        job["steps"].append("kmeans_for_xy")
        labels = run_kmeans(vectors, k=3)
        xy_all = assign_cluster_xy(labels)

        payloads = []
        for i in dense_indices:
            row = rows[i]
            id_, summary, fullOpinion, _x, _y, _density = row
            rx, ry = xy_all[i]

            payloads.append({
                "id": id_,
                "cluster_id": "",
                "x": rx,
                "y": ry,
                "summary": summary,
                "fullOpinion": fullOpinion,
                "density": dens_norm[i],
            })

        job["steps"].append("write_db")
        write_opinions(TABLE_OPINIONS_DENSE, payloads)

        _finish_job(job, "success")
        return {"status": "ok", "count": len(payloads)}

    except Exception as e:
        _finish_job(job, "error", str(e))
        raise
