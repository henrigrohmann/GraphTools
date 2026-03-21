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

ー    cluster_list, argument_list = _build_hierarchy_payload(mode)
    write_hierarchy(table_map[mode], cluster_list, argument_list)
    return read_hierarchy(table_map[mode])


def _build_argument(opinion: dict) -> dict:
    return {
        "id": opinion.get("id"),
        "summary": opinion.get("summary", ""),
        "fullOpinion": opinion.get("fullOpinion", ""),
        "children": [],
        "cluster_id": opinion.get("cluster_id", ""),
        "density": opinion.get("density"),
    }


def _build_cluster_entry(cluster_id: str, label: str, member_ids: list[str]) -> dict:
    return {
        "id": cluster_id,
        "label": label,
        "summary": label,
        "memberIds": member_ids,
    }


def _build_hierarchy_payload(mode: str) -> tuple[list[dict], list[dict]]:
    if mode == "cluster":
        opinions = read_opinions(TABLE_OPINIONS_CLUSTERED)
        groups: dict[str, list[dict]] = {}
        for opinion in opinions:
            cluster_id = opinion.get("cluster_id") or "unassigned"
            groups.setdefault(cluster_id, []).append(opinion)

        cluster_list = []
        argument_list = []
        for cluster_id in sorted(groups):
            members = groups[cluster_id]
            member_ids = [member["id"] for member in members]
            cluster_list.append(
                _build_cluster_entry(cluster_id, f"cluster:{cluster_id}", member_ids)
            )
            argument_list.extend(_build_argument(member) for member in members)
        return cluster_list, argument_list

    if mode == "dense":
        opinions = read_opinions(TABLE_OPINIONS_DENSE)
        sorted_ops = sorted(
            opinions,
            key=lambda opinion: opinion.get("density") or 0.0,
            reverse=True,
        )
        top_members = sorted_ops[:5]
        other_members = sorted_ops[5:]

        cluster_list = [
            _build_cluster_entry(
                "dense-top",
                "dense-top",
                [member["id"] for member in top_members],
            ),
            _build_cluster_entry(
                "dense-other",
                "dense-other",
                [member["id"] for member in other_members],
            ),
        ]
        argument_list = [_build_argument(opinion) for opinion in sorted_ops]
        return cluster_list, argument_list

    opinions = read_opinions(TABLE_OPINIONS_RAW)
    cluster_list = [
        _build_cluster_entry(
            "external-all",
            "external-all",
            [opinion["id"] for opinion in opinions],
        )
    ]
    argument_list = [_build_argument(opinion) for opinion in opinions]
    return cluster_list, argument_list


@app.get("/hierarchy_dump")
def hierarchy_dump(mode: str):
    return api_hierarchy(mode)


@app.get("/jobs")
def jobs():
    job_list = read_jobs()
    return {"count": len(job_list), "jobs": job_list}

