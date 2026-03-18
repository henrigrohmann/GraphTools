from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from pipeline import (
    run_init_pipeline,
    run_raw_pipeline,
    run_cluster_pipeline,
    load_scatter_data,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/init")
def init():
    """CSV → DB 初期登録（とりあえず全件をDBに入れるだけ）"""
    logs = run_init_pipeline()
    return {"status": "ok", "logs": logs}

@app.get("/raw")
def raw():
    """生データ：ランダム座標・クラスタなしでDBを上書き"""
    logs = run_raw_pipeline()
    return {"status": "ok", "logs": logs}

@app.get("/cluster")
def cluster():
    """クラスタリング：なんちゃってk-meansでクラスタ＋座標を再計算してDBを上書き"""
    logs = run_cluster_pipeline()
    return {"status": "ok", "logs": logs}

@app.get("/scatter")
def scatter():
    """現在のDB状態を scatter 用データとして返す"""
    return load_scatter_data()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
