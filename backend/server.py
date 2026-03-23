import csv
import json
import sqlite3
from pathlib import Path
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

# --- plugins ---
from plugins.vectorizer_hash import vectorize_hash
from plugins.cluster_kmeans import run_kmeans
from plugins.layout_centering import assign_xy

DB_PATH = "graph.db"
DATA_CSV = "data30.csv"
CLUSTER_CSV = "cluster30.csv"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    seq = 0

    # -----------------------------------------
    # CSV をテキストとして読み込む（BOM 除去）
    # -----------------------------------------
    with path.open(encoding="utf-8") as f:
        text = f.read().replace("\ufeff", "").strip()

    # csv.reader で正確にカラム数を判定
    import io
    reader = csv.reader(io.StringIO(text))
    rows = [r for r in reader if any(cell.strip() for cell in r)]

    if len(rows) == 0:
        conn.close()
        return {"loaded": False, "reason": "CSV empty"}

    # -----------------------------------------
    # ① 1カラム CSV 判定
    # -----------------------------------------
    is_single_column = all(len(r) == 1 for r in rows)

    if is_single_column:
        # fullOpinion のリスト
        fulls = [r[0].strip() for r in rows]

        # 1) ハッシュベクトル化
        vecs = vectorize_hash(fulls)

        # 2) なんちゃって k-means
        k = 3
        cluster_ids = run_kmeans(vecs, k=k)

        # 3) 中心寄せで座標生成
        xs, ys = assign_xy(cluster_ids, k=k)

        # 4) DB に保存
        for idx, full in enumerate(fulls):
            seq += 1
            cur.execute("""
                INSERT OR REPLACE INTO scatter_raw
                (id, x, y, cluster_id, summary, title)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                f"auto-{seq:04d}",
                xs[idx],
                ys[idx],
                str(cluster_ids[idx]),
                full[:30],
                full
            ))

        conn.commit()
        conn.close()
        return {"loaded": True, "mode": "single-column"}

    # -----------------------------------------
    # ② 通常 CSV（2カラム以上）
    # -----------------------------------------
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            seq += 1
            raw_id = str(row.get("id", "") or "").strip()
            if raw_id.lower() == "id":
                continue
            if not raw_id:
                raw_id = f"auto-{seq:04d}"

            try:
                x = float(row.get("x", "") or 0)
                y = float(row.get("y", "") or 0)
            except:
                x, y = 0, 0

            cid = row.get("cluster_id") or row.get("clusterId") or None

            cur.execute("""
                INSERT OR REPLACE INTO scatter_raw
                (id, x, y, cluster_id, summary, title)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                raw_id,
                x,
                y,
                cid,
                row.get("summary", ""),
                row.get("title", "")
            ))

    conn.commit()
    conn.close()
    return {"loaded": True, "mode": "multi-column"}

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
# /filter（cluster 絞り込み）
# ============================================================

@app.get("/filter")
def filter_api(cluster: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM scatter_raw WHERE cluster_id = ?",
        (cluster,)
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# ============================================================
# /dump
# ============================================================

@app.get("/dump")
def dump():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM scatter_raw")
    scatter_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM hierarchy")
    hierarchy_count = cur.fetchone()[0]

    cur.execute("SELECT json FROM hierarchy WHERE id = ?", ("root",))
    row = cur.fetchone()
    hierarchy_json = json.loads(row["json"]) if row else {}

    conn.close()

    return {
        "tables": {
            "scatter_raw": scatter_count,
            "hierarchy": hierarchy_count,
        },
        "hierarchy": hierarchy_json,
        "recent_jobs": []
    }

# ============================================================
# /health
# ============================================================

@app.get("/health")
def health():
    return {"status": "ok"}
