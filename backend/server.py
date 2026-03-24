# ============================================================
# GraphTool v1.8.1 backend (server.py)
# ============================================================

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import uvicorn

from pipeline import (
    init_pipeline,
    load_data_csv,
    get_scatter_data,
    get_hierarchy_data,
    filter_by_cluster,
    dump_all,
    health_check,
)

app = FastAPI()

# ------------------------------------------------------------
# ★ Windows で CSV が壊れる原因を修正：絶対パス化
# ------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_CSV = BASE_DIR / "temp_upload.csv"

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
# /init
# ------------------------------------------------------------
@app.post("/init")
def init():
    data, cluster = init_pipeline()
    return {"data": data, "cluster": cluster}

# ------------------------------------------------------------
# /upload
# ------------------------------------------------------------
@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    # 保存先は server.py と同じディレクトリ
    with open(UPLOAD_CSV, "wb") as f:
        f.write(await file.read())

    # CSV をロード
    load_data_csv(str(UPLOAD_CSV))

    return {"status": "ok", "file": file.filename}

# ------------------------------------------------------------
# /scatter
# ------------------------------------------------------------
@app.get("/scatter")
def scatter(mode: str = "raw"):
    return get_scatter_data(mode)

# ------------------------------------------------------------
# /hierarchy
# ------------------------------------------------------------
@app.get("/hierarchy")
def hierarchy(mode: str = "cluster"):
    return get_hierarchy_data(mode)

# ------------------------------------------------------------
# /filter
# ------------------------------------------------------------
@app.get("/filter")
def filter_api(cluster: str):
    return filter_by_cluster(cluster)

# ------------------------------------------------------------
# /dump
# ------------------------------------------------------------
@app.get("/dump")
def dump():
    return dump_all()

# ------------------------------------------------------------
# /health
# ------------------------------------------------------------
@app.get("/health")
def health():
    return health_check()

# ------------------------------------------------------------
# main
# ------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)
