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
        delete_hierarchy,
        write_hierarchy,
        read_hierarchy,
        TABLE_OPINIONS_RAW,
        TABLE_OPINIONS_RANDOM,
        TABLE_OPINIONS_CLUSTERED,
        TABLE_OPINIONS_DENSE,
        TABLE_HIERARCHY_EXTERNAL,
        TABLE_HIERARCHY_CLUSTER,
        TABLE_HIERARCHY_DENSE,
    )
    # from .plugins.hierarchy_loader import load_hierarchy_csv
except ImportError:
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
        delete_hierarchy,
        write_hierarchy,
        read_hierarchy,
        TABLE_OPINIONS_RAW,
        TABLE_OPINIONS_RANDOM,
        TABLE_OPINIONS_CLUSTERED,
        TABLE_OPINIONS_DENSE,
        TABLE_HIERARCHY_EXTERNAL,
        TABLE_HIERARCHY_CLUSTER,
        TABLE_HIERARCHY_DENSE,
    )
    # from plugins.hierarchy_loader import load_hierarchy_csv

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# RAW
# ---------------------------------------------------------
@app.get("/raw")
def pipeline_raw():
    try:
        rows = load_csv()

        # 階層データは全削除
        delete_hierarchy("all")

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
                "fullOpinion": fullOpinion,
                "density": None,
            })

        write_opinions(TABLE_OPINIONS_RAW, payloads)

        log_job({"pipeline": "raw", "status": "success", "count": len(payloads)})
        return {"status": "ok", "count": len(payloads)}

    except Exception as e:
        log_job({"pipeline": "raw", "status": "error", "error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------
# RANDOM
# ---------------------------------------------------------
@app.get("/random")
def pipeline_random():
    try:
        rows = load_csv()

        delete_hierarchy("all")

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

        write_opinions(TABLE_OPINIONS_RANDOM, payloads)

        log_job({"pipeline": "random", "status": "success", "count": len(payloads)})
        return {"status": "ok", "count": len(payloads)}

    except Exception as e:
        log_job({"pipeline": "random", "status": "error", "error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------
# CLUSTER
# ---------------------------------------------------------
@app.get("/cluster")
def pipeline_cluster():
    try:
        rows = load_csv()

        delete_hierarchy("cluster")

        rows_for_vec = [(r[0], r[1], r[2], r[3], r[4]) for r in rows]
        vectors = vectorize(rows_for_vec)
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
                "fullOpinion": fullOpinion,
                "density": None,
            })

        write_opinions(TABLE_OPINIONS_CLUSTERED, payloads)

        log_job({"pipeline": "cluster", "status": "success", "count": len(payloads)})
        return {"status": "ok", "count": len(payloads)}

    except Exception as e:
        log_job({"pipeline": "cluster", "status": "error", "error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------
# DENSE
# ---------------------------------------------------------
@app.get("/dense")
def pipeline_dense():
    try:
        rows = load_csv()

        delete_hierarchy("dense")

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
                "fullOpinion": fullOpinion,
                "density": density,
            })

        write_opinions(TABLE_OPINIONS_DENSE, payloads)

        log_job({"pipeline": "dense", "status": "success", "count": len(payloads)})
        return {"status": "ok", "count": len(payloads)}

    except Exception as e:
        log_job({"pipeline": "dense", "status": "error", "error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------
# SCATTER
# ---------------------------------------------------------
@app.get("/scatter")
def get_scatter(mode: str):
    table_map = {
        "raw": TABLE_OPINIONS_RAW,
        "random": TABLE_OPINIONS_RANDOM,
        "cluster": TABLE_OPINIONS_CLUSTERED,
        "dense": TABLE_OPINIONS_DENSE,
    }

    if mode not in table_map:
        raise HTTPException(status_code=400, detail="invalid mode")

    data = read_opinions(table_map[mode])
    return {"count": len(data), "data": data}


# ---------------------------------------------------------
# HIERARCHY
# ---------------------------------------------------------
@app.get("/hierarchy")
def api_hierarchy(mode: str):
    """
    mode = external | cluster | dense
    """

    table_map = {
        "external": TABLE_HIERARCHY_EXTERNAL,
        "cluster": TABLE_HIERARCHY_CLUSTER,
        "dense": TABLE_HIERARCHY_DENSE,
    }

    if mode not in table_map:
        raise HTTPException(status_code=400, detail="invalid mode")

    # 既存データがあれば返す
    existing = read_hierarchy(table_map[mode])
    if existing:
        return existing

    # ここで階層データを生成する（現時点ではなんちゃってのみ）
    if mode == "cluster":
        ops = read_opinions(TABLE_OPINIONS_CLUSTERED)

        # cluster_id ごとに argumentList を生成
        argumentList = []
        cluster_groups = {}

        for op in ops:
            uid = op["id"]
            cid = op["cluster_id"]
            if cid not in cluster_groups:
                cluster_groups[cid] = []
           
