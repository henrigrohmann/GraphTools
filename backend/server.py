from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from pipeline import (
    run_raw_pipeline,
    run_random_pipeline,
    run_cluster_pipeline,
)
from writer_db import (
    read_opinions,
    read_jobs,
    TABLE_OPINIONS_RAW,
    TABLE_OPINIONS_RANDOM,
    TABLE_OPINIONS_CLUSTERED,
)

app = FastAPI()

# CORS 全許可（デモ用途）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/raw")
def api_raw():
    """
    CSV → 座標そのまま or ランダム → opinions_raw に保存
    """
    try:
        result = run_raw_pipeline()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/random")
def api_random():
    """
    CSV → 座標無視してランダム → opinions_random に保存
    """
    try:
        result = run_random_pipeline()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cluster")
def api_cluster():
    """
    CSV → ベクトル化 → k-means → 座標生成 → opinions_clustered に保存
    """
    try:
        result = run_cluster_pipeline()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/scatter")
def api_scatter(mode: str):
    """
    mode = raw | random | cluster
    """
    if mode == "raw":
        table = TABLE_OPINIONS_RAW
    elif mode == "random":
        table = TABLE_OPINIONS_RANDOM
    elif mode == "cluster":
        table = TABLE_OPINIONS_CLUSTERED
    else:
        raise HTTPException(status_code=400, detail="Invalid mode")

    try:
        data = read_opinions(table)
        return {"count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs")
def api_jobs():
    """
    JOB ログ一覧
    """
    try:
        logs = read_jobs()
        return {"count": len(logs), "jobs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
