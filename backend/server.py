import csv
import json
import sqlite3
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query

DB_PATH = "graph.db"
DATA_CSV = "data30.csv"
CLUSTER_CSV = "cluster30.csv"

app = FastAPI()


# ============================================================
# DB 接続
# ============================================================

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# DB 初期化
# ============================================================

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS scatter_raw (
            id TEXT PRIMARY KEY,
            x REAL,
            y REAL,
            cluster_id TEXT,
            summary TEXT,
            title TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS hierarchy (
            id TEXT PRIMARY KEY,
            json TEXT
        )
    """)

    conn.commit()
    conn.close()


# ============================================================
# CSV ロード（data30.csv）
# ============================================================

def load_data_csv():
    path = Path(DATA_CSV)
    if not path.exists():
        return {"loaded": False, "reason": f"{DATA_CSV} not found"}

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM scatter_raw")

    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                x = float(row.get("x", "") or 0)
                y = float(row.get("y", "") or 0)
            except:
                x, y = 0, 0

            cid = row.get("cluster_id") or row.get("clusterId") or ""
            cid = str(cid) if cid != "" else None

            cur.execute("""
                INSERT INTO scatter_raw (id, x, y, cluster_id, summary, title)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                row.get("id"),
                x,
                y,
                cid,
                row.get("summary", ""),
                row.get("title", "")
            ))

    conn.commit()
    conn.close()

    return {"loaded": True}


# ============================================================
# scatter_raw → 階層生成（cluster30.csv が無い場合）
# ============================================================

def build_hierarchy_from_scatter():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, cluster_id, summary, title FROM scatter_raw")
    rows = cur.fetchall()
    conn.close()

    groups = {}
    for r in rows:
        raw_cid = r["cluster_id"]
        cid = str(raw_cid) if raw_cid not in (None, "") else "unassigned"
        groups.setdefault(cid, []).append(r)

    cluster_list = []
    for cid, members in groups.items():
        cluster_list.append({
            "id": cid,
            "label": cid,
            "memberIds": [m["id"] for m in members],
        })

    argument_list = []
    for r in rows:
        argument_list.append({
            "id": r["id"],
            "summary": r["summary"],
            "fullOpinion": r["title"],
        })

    return {
        "clusterList": cluster_list,
        "argumentList": argument_list,
    }


# ============================================================
# cluster30.csv があれば読む、無ければ scatter_raw から生成
# ============================================================

def load_cluster_csv_or_build():
    path = Path(CLUSTER_CSV)
    conn = get_conn()
    cur = conn.cursor()

    if path.exists():
        # cluster30.csv がある場合はそのまま読み込む
        with path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            obj = {
                "clusterList": [],
                "argumentList": []
            }
            for row in reader:
                cid = str(row.get("cluster_id") or row.get("clusterId") or "unassigned")
                obj["clusterList"].append({
                    "id": cid,
                    "label": cid,
                    "memberIds": row.get("memberIds", "").split()
                })

        cur.execute(
            "INSERT OR REPLACE INTO hierarchy (id, json) VALUES (?, ?)",
            ("root", json.dumps(obj, ensure_ascii=False)),
        )
        conn.commit()
        conn.close()
        return {"loaded": True, "source": "cluster_csv"}

    # cluster30.csv が無い → scatter_raw から生成
    obj = build_hierarchy_from_scatter()
    cur.execute(
        "INSERT OR REPLACE INTO hierarchy (id, json) VALUES (?, ?)",
        ("root", json.dumps(obj, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()
    return {"loaded": False, "source": "scatter_raw", "reason": "cluster30.csv not found"}


# ============================================================
# /init
# ============================================================

@app.post("/init")
def init():
    init_db()
    data_result = load_data_csv()
    cluster_result = load_cluster_csv_or_build()

    return {
        "data": data_result,
        "cluster": cluster_result,
    }


# ============================================================
# /hierarchy
# ============================================================

@app.get("/hierarchy")
def hierarchy(mode: str = Query("cluster")):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT json FROM hierarchy WHERE id = ?", ("root",))
    row = cur.fetchone()
    conn.close()

    if not row:
        return build_hierarchy_from_scatter()

    try:
        return json.loads(row["json"])
    except:
        return build_hierarchy_from_scatter()


# ============================================================
# /scatter
# ============================================================

@app.get("/scatter")
def scatter(mode: str = Query("raw")):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM scatter_raw")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# ============================================================
# /health
# ============================================================

@app.get("/health")
def health():
    return {"status": "ok"}
