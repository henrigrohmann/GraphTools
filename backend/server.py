from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

try:
    from .plugins.loader_csv import load_csv
    from .plugins.vectorizer_simple import vectorize
    from .plugins.cluster_kmeans import run_kmeans
    from .plugins.layout_random import assign_random_xy
    from .plugins.layout_scatter import assign_xy as assign_cluster_xy
    from .plugins.writer_db import (
        write_opinions,
        read_opinions,
        log_job,
        read_jobs,
        TABLE_OPINIONS_RAW,
        TABLE_OPINIONS_RANDOM,
        TABLE_OPINIONS_CLUSTERED,
    )
except ImportError:
    # Fallback for direct script execution.
    from plugins.loader_csv import load_csv
    from plugins.vectorizer_simple import vectorize
    from plugins.cluster_kmeans import run_kmeans
    from plugins.layout_random import assign_random_xy
    from plugins.layout_scatter import assign_xy as assign_cluster_xy
    from plugins.writer_db import (
        write_opinions,
        read_opinions,
        log_job,
        read_jobs,
        TABLE_OPINIONS_RAW,
        TABLE_OPINIONS_RANDOM,
        TABLE_OPINIONS_CLUSTERED,
    )

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/raw")
def pipeline_raw():
    """
    CSV → 座標そのまま or ランダム → opinions_raw に保存
    """
    try:
        rows = load_csv()
        xy_list = []
        for (id_, summary, fullOpinion, x, y, density) in rows:
            if x is None or y is None:
                rx, ry = assign_random_xy(1)[0]
            else:
                rx, ry = x, y
            xy_list.append((rx, ry))

        payloads = []
        for (row, (rx, ry)) in zip(rows, xy_list):
            id_, summary, fullOpinion, x, y, density = row
            payloads.append({
                "id": id_,
                "cluster_id": "",
                "x": rx,
                "y": ry,
                "summary": summary,
                "fullOpinion": fullOpinion
            })

        write_opinions(TABLE_OPINIONS_RAW, payloads)

        log_job({
            "pipeline": "raw",
            "status": "success",
            "count": len(payloads),
        })

        return {"status": "ok", "count": len(payloads)}
    except Exception as e:
        log_job({
            "pipeline": "raw",
            "status": "error",
            "error": str(e),
        })
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/random")
def pipeline_random():
    """
    CSV → 座標無視してランダム → opinions_random に保存
    """
    try:
        rows = load_csv()
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
                "fullOpinion": fullOpinion
            })

        write_opinions(TABLE_OPINIONS_RANDOM, payloads)

        log_job({
            "pipeline": "random",
            "status": "success",
            "count": len(payloads),
        })

        return {"status": "ok", "count": len(payloads)}
    except Exception as e:
        log_job({
            "pipeline": "random",
            "status": "error",
            "error": str(e),
        })
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cluster")
def pipeline_cluster():
    """
    CSV → ベクトル化 → k-means → 座標生成 → opinions_clustered に保存
    """
    try:
        rows = load_csv()
        vectors = vectorize(rows)
        labels = run_kmeans(vectors, k=3)
        xy = assign_cluster_xy(labels)

        payloads = []
        for (row, label, (rx, ry)) in zip(rows, labels, xy):
            id_, summary, fullOpinion, x, y, density = row
            cluster_name = ["A", "B", "C"][label % 3]

            payloads.append({
                "id": id_,
                "cluster_id": cluster_name,
                "x": rx,
                "y": ry,
                "summary": summary,
                "fullOpinion": fullOpinion
            })

        write_opinions(TABLE_OPINIONS_CLUSTERED, payloads)

        log_job({
            "pipeline": "cluster",
            "status": "success",
            "count": len(payloads),
        })

        return {"status": "ok", "count": len(payloads)}
    except Exception as e:
        log_job({
            "pipeline": "cluster",
            "status": "error",
            "error": str(e),
        })
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/scatter")
def get_scatter(mode: str):
    """
    mode = raw | random | cluster
    """
    table_map = {
        "raw": TABLE_OPINIONS_RAW,
        "random": TABLE_OPINIONS_RANDOM,
        "cluster": TABLE_OPINIONS_CLUSTERED,
    }

    if mode not in table_map:
        raise HTTPException(status_code=400, detail="invalid mode")

    data = read_opinions(table_map[mode])
    return {"count": len(data), "data": data}


@app.get("/jobs")
def api_jobs():
    """
    JOB ログ一覧
    """
    logs = read_jobs()
    return {"count": len(logs), "jobs": logs}
