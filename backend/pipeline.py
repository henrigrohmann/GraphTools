import uuid
from datetime import datetime
import traceback

try:
    from .plugins.loader_csv import load_csv
    from .plugins.vectorizer_simple import vectorize
    from .plugins.cluster_kmeans import run_kmeans
    from .plugins.layout_random import assign_random_xy
    from .plugins.layout_scatter import assign_xy as assign_cluster_xy
    from .plugins.density_knn import compute_density

    from .plugins.writer_db import (
        write_opinions,
        log_job,
        TABLE_OPINIONS_RAW,
        TABLE_OPINIONS_RANDOM,
        TABLE_OPINIONS_CLUSTERED,
        TABLE_OPINIONS_DENSE,
    )
except ImportError:
    from plugins.loader_csv import load_csv
    from plugins.vectorizer_simple import vectorize
    from plugins.cluster_kmeans import run_kmeans
    from plugins.layout_random import assign_random_xy
    from plugins.layout_scatter import assign_xy as assign_cluster_xy
    from plugins.density_knn import compute_density

    from plugins.writer_db import (
        write_opinions,
        log_job,
        TABLE_OPINIONS_RAW,
        TABLE_OPINIONS_RANDOM,
        TABLE_OPINIONS_CLUSTERED,
        TABLE_OPINIONS_DENSE,
    )


# ============================================================
#  Utility
# ============================================================

def _now_iso():
    return datetime.utcnow().isoformat(timespec="seconds")


def _log(job: dict, msg: str):
    """Evidence Log に1行追加"""
    job["logs"].append(f"[{_now_iso()}] {msg}")


# ============================================================
#  Job Management (future-ready: async / retry / timeout)
# ============================================================

def _start_job(pipeline_name: str) -> dict:
    job_id = f"{pipeline_name}-{_now_iso().replace(':','').replace('-','')}-{uuid.uuid4().hex[:6]}"
    return {
        "job_id": job_id,
        "pipeline": pipeline_name,
        "mode": "sync",        # ← 将来 async に拡張可能
        "queue": "default",    # ← 将来のキュー名
        "retry": 0,            # ← 将来のリトライ回数
        "max_retry": 3,        # ← 将来のリトライ上限
        "status": "running",
        "started_at": _now_iso(),
        "finished_at": None,
        "duration_ms": None,
        "steps": [],
        "logs": [],            # ← Evidence Log
        "error": None,
        "timeout_ms": 30000,   # ← 将来の worker が参照
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
        _log(job, f"JOB ERROR: {error}")

    log_job(job)


# ============================================================
#  RAW PIPELINE
# ============================================================

def run_raw_pipeline(csv_path: str | None = None):
    job = _start_job("raw")
    try:
        job["steps"].append("load_csv")
        _log(job, "START load_csv")
        rows = load_csv(csv_path)
        _log(job, f"END load_csv (count={len(rows)})")

        payloads = []
        for (id_, summary, fullOpinion, x, y, _density) in rows:
            if x is None or y is None:
                job["steps"].append("assign_random_xy")
                _log(job, "assign_random_xy (fallback)")
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
        _log(job, f"START write_db (count={len(payloads)})")
        write_opinions(TABLE_OPINIONS_RAW, payloads)
        _log(job, "END write_db")

        _finish_job(job, "success")
        return {"status": "ok", "count": len(payloads), "job": job}

    except Exception as e:
        _log(job, f"EXCEPTION: {e}")
        _log(job, traceback.format_exc())
        _finish_job(job, "error", str(e))
        raise


# ============================================================
#  RANDOM PIPELINE
# ============================================================

def run_random_pipeline(csv_path: str | None = None):
    job = _start_job("random")
    try:
        job["steps"].append("load_csv")
        _log(job, "START load_csv")
        rows = load_csv(csv_path)
        _log(job, f"END load_csv (count={len(rows)})")

        job["steps"].append("assign_random_xy")
        _log(job, "START assign_random_xy")
        xy = assign_random_xy(len(rows))
        _log(job, "END assign_random_xy")

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
        _log(job, f"START write_db (count={len(payloads)})")
        write_opinions(TABLE_OPINIONS_RANDOM, payloads)
        _log(job, "END write_db")

        _finish_job(job, "success")
        return {"status": "ok", "count": len(payloads), "job": job}

    except Exception as e:
        _log(job, f"EXCEPTION: {e}")
        _log(job, traceback.format_exc())
        _finish_job(job, "error", str(e))
        raise


# ============================================================
#  CLUSTER PIPELINE
# ============================================================

def run_cluster_pipeline(csv_path: str | None = None):
    job = _start_job("cluster")
    try:
        job["steps"].append("load_csv")
        _log(job, "START load_csv")
        rows = load_csv(csv_path)
        _log(job, f"END load_csv (count={len(rows)})")

        job["steps"].append("vectorize")
        _log(job, "START vectorize")
        texts = [fullOpinion for (_, _, fullOpinion, _, _, _) in rows]
        vectors = vectorize(texts)
        _log(job, f"END vectorize (dim={len(vectors[0]) if vectors else 0})")

        job["steps"].append("kmeans")
        _log(job, "START kmeans (k=3)")
        labels = run_kmeans(vectors, k=3)
        _log(job, "END kmeans")

        job["steps"].append("assign_cluster_xy")
        _log(job, "START assign_cluster_xy")
        xy = assign_cluster_xy(labels)
        _log(job, "END assign_cluster_xy")

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
        _log(job, f"START write_db (count={len(payloads)})")
        write_opinions(TABLE_OPINIONS_CLUSTERED, payloads)
        _log(job, "END write_db")

        _finish_job(job, "success")
        return {"status": "ok", "count": len(payloads), "job": job}

    except Exception as e:
        _log(job, f"EXCEPTION: {e}")
        _log(job, traceback.format_exc())
        _finish_job(job, "error", str(e))
        raise


# ============================================================
#  DENSE PIPELINE
# ============================================================

def run_dense_pipeline(csv_path: str | None = None):
    job = _start_job("dense")
    try:
        job["steps"].append("load_csv")
        _log(job, "START load_csv")
        rows = load_csv(csv_path)
        _log(job, f"END load_csv (count={len(rows)})")

        if not rows:
            _log(job, "NO ROWS, EXIT")
            _finish_job(job, "success")
            return {"status": "ok", "count": 0, "job": job}

        job["steps"].append("vectorize")
        _log(job, "START vectorize")
        texts = [fullOpinion for (_, _, fullOpinion, _, _, _) in rows]
        vectors = vectorize(texts)
        _log(job, f"END vectorize (dim={len(vectors[0]) if vectors else 0})")

        job["steps"].append("compute_density")
        _log(job, "START compute_density (k=5)")
        dens_norm = compute_density(vectors, k=5)
        _log(job, "END compute_density")

        job["steps"].append("select_top")
        _log(job, "START select_top (top=20%)")
        sorted_d = sorted(dens_norm)
        threshold = sorted_d[int(len(sorted_d) * 0.8)] if len(sorted_d) > 1 else sorted_d[0]
        dense_indices = [i for i, d in enumerate(dens_norm) if d >= threshold]
        _log(job, f"END select_top (selected={len(dense_indices)})")

        job["steps"].append("kmeans_for_xy")
        _log(job, "START kmeans_for_xy (k=3)")
        labels = run_kmeans(vectors, k=3)
        xy_all = assign_cluster_xy(labels)
        _log(job, "END kmeans_for_xy")

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
        _log(job, f"START write_db (count={len(payloads)})")
        write_opinions(TABLE_OPINIONS_DENSE, payloads)
        _log(job, "END write_db")

        _finish_job(job, "success")
        return {"status": "ok", "count": len(payloads), "job": job}

    except Exception as e:
        _log(job, f"EXCEPTION: {e}")
        _log(job, traceback.format_exc())
        _finish_job(job, "error", str(e))
        raise
