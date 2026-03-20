from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from plugins.loader_csv import load_csv
from plugins.vectorizer_simple import vectorize
from plugins.cluster_kmeans import run_kmeans
from plugins.layout_random import assign_random_xy
from plugins.layout_scatter import assign_xy
from plugins.writer_db import (
    write_opinions,
    read_opinions,
    log_job,
    read_jobs,
    reset_opinions_tables,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/init")
def init_pipeline():
    """
    データテーブルを初期化する（jobs_log は残す）。
    """
    try:
        reset_opinions_tables()

        log_job({
            "pipeline": "init",
            "status": "success",
            "message": "opinions tables cleared",
        }, is_debug=False)

        return {"status": "ok", "message": "initialized"}
    except Exception as e:
        log_job({
            "pipeline": "init",
            "status": "error",
            "error": str(e),
        })
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/raw")
def pipeline_raw():
    """
    CSV を読み込み、ランダム座標を付与して raw テーブルに保存。
    """
    try:
        rows = load_csv()
        xy = assign_random_xy(len(rows))

        payloads = []
        for (row, (rx, ry)) in zip(rows, xy):
            id_, summary, fullOpinion, x, y = row
            payloads.append({
                "id": id_,
                "cluster_id": "",
                "x": rx,
                "y": ry,
                "summary": summary,
                "fullOpinion": fullOpinion,
            })

        write_opinions("opinions_raw", payloads, is_debug=False)

        log_job({
            "pipeline": "raw",
            "status": "success",
            "count": len(payloads),
        }, is_debug=False)

        return {"status": "ok", "count": len(payloads)}
    except Exception as e:
        log_job({
            "pipeline": "raw",
            "status": "error",
            "error": str(e),
        })
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cluster")
def pipeline_cluster():
    """
    CSV を読み込み、クラスタリングして clustered テーブルに保存。
    """
    try:
        rows = load_csv()
        vectors = vectorize(rows)
        labels = run_kmeans(vectors, k=3)
        xy = assign_xy(labels)

        payloads = []
        for (row, label, (rx, ry)) in zip(rows, labels, xy):
            id_, summary, fullOpinion, x, y = row
            cluster_name = ["A", "B", "C"][label % 3]

            payloads.append({
                "id": id_,
                "cluster_id": cluster_name,
                "x": rx,
                "y": ry,
                "summary": summary,
                "fullOpinion": fullOpinion,
            })

        write_opinions("opinions_clustered", payloads, is_debug=False)

        log_job({
            "pipeline": "cluster",
            "status": "success",
            "count": len(payloads),
        }, is_debug=False)

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
    mode = raw / random / cluster
    """
    table_map = {
        "raw": "opinions_raw",
        "random": "opinions_random",
        "cluster": "opinions_clustered",
    }

    if mode not in table_map:
        raise HTTPException(status_code=400, detail="invalid mode")

    data = read_opinions(table_map[mode])
    return {"count": len(data), "data": data}


@app.get("/jobs")
def get_jobs():
    return {"count": len(read_jobs()), "data": read_jobs()}
