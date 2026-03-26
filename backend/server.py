# ============================================================
# GraphTool backend (server.py) CSV パス対応版
# ============================================================

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import uvicorn

# ------------------------------------------------------------
# パス設定（Codespaces / Windows 両対応）
# ------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
UPLOAD_CSV = str(UPLOAD_DIR / "temp_upload.csv")

# ------------------------------------------------------------
# pipeline（DB 書き込み）
# ------------------------------------------------------------
from pipeline import (
    run_raw_pipeline,
    run_random_pipeline,
    run_cluster_pipeline,
    run_dense_pipeline,   # ★ 追加済み
)

# ------------------------------------------------------------
# DB 読み出し（writer_db）
# ------------------------------------------------------------
from plugins.writer_db import (
    read_opinions,
    read_hierarchy,
    read_jobs,
    TABLE_OPINIONS_RAW,
    TABLE_OPINIONS_RANDOM,
    TABLE_OPINIONS_CLUSTERED,
    TABLE_OPINIONS_DENSE,
    TABLE_HIERARCHY_EXTERNAL,
    TABLE_HIERARCHY_CLUSTER,
    TABLE_HIERARCHY_DENSE,
)

app = FastAPI()

# ------------------------------------------------------------
# CORS
# ------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------
# /init → GET/POST 両対応に変更
# ------------------------------------------------------------
@app.post("/init")
@app.get("/init")   # ← ★ 追加
def init():
    raw_result = run_raw_pipeline(csv_path=None)
    random_result = run_random_pipeline(csv_path=None)
    cluster_result = run_cluster_pipeline(csv_path=None)
    dense_result = run_dense_pipeline(csv_path=None)

    return {
        "status": "ok",
        "raw": raw_result,
        "random": random_result,
        "cluster": cluster_result,
        "dense": dense_result,
    }

# ------------------------------------------------------------
# /upload → CSV を保存して raw/cluster/dense を再生成
# ------------------------------------------------------------
@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    with open(UPLOAD_CSV, "wb") as f:
        f.write(await file.read())

    raw_result = run_raw_pipeline(csv_path=UPLOAD_CSV)
    cluster_result = run_cluster_pipeline(csv_path=UPLOAD_CSV)
    dense_result = run_dense_pipeline(csv_path=UPLOAD_CSV)

    return {
        "status": "ok",
        "file": file.filename,
        "raw": raw_result,
        "cluster": cluster_result,
        "dense": dense_result,
    }

# ------------------------------------------------------------
# /scatter
# ------------------------------------------------------------
@app.get("/scatter")
def scatter(mode: str = "raw"):
    if mode == "raw":
        return read_opinions(TABLE_OPINIONS_RAW)
    elif mode == "random":
        return read_opinions(TABLE_OPINIONS_RANDOM)
    elif mode == "cluster":
        return read_opinions(TABLE_OPINIONS_CLUSTERED)
    elif mode == "dense":
        return read_opinions(TABLE_OPINIONS_DENSE)
    else:
        return {"error": "invalid mode"}

# ------------------------------------------------------------
# /hierarchy
# ------------------------------------------------------------
@app.get("/hierarchy")
def hierarchy(mode: str = "cluster"):
    if mode == "external":
        return read_hierarchy(TABLE_HIERARCHY_EXTERNAL)
    elif mode == "cluster":
        return read_hierarchy(TABLE_HIERARCHY_CLUSTER)
    elif mode == "dense":
        return read_hierarchy(TABLE_HIERARCHY_DENSE)
    else:
        return {"error": "invalid mode"}

# ------------------------------------------------------------
# /filter
# ------------------------------------------------------------
@app.get("/filter")
def filter_api(cluster: str):
    rows = read_opinions(TABLE_OPINIONS_CLUSTERED)
    filtered = [r for r in rows if r.get("cluster_id") == cluster]
    return filtered

# ------------------------------------------------------------
# /dump
# ------------------------------------------------------------
@app.get("/dump")
def dump():
    return {
        "tables": {
            "raw": len(read_opinions(TABLE_OPINIONS_RAW)),
            "random": len(read_opinions(TABLE_OPINIONS_RANDOM)),
            "clustered": len(read_opinions(TABLE_OPINIONS_CLUSTERED)),
            "dense": len(read_opinions(TABLE_OPINIONS_DENSE)),
        },
        "jobs": read_jobs(),
        "hierarchy_cluster": read_hierarchy(TABLE_HIERARCHY_CLUSTER),
    }

# ------------------------------------------------------------
# /health
# ------------------------------------------------------------
@app.get("/health")
def health():
    try:
        _ = read_opinions(TABLE_OPINIONS_RAW)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

# ------------------------------------------------------------
# main
# ------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)
