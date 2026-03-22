# server.py
#
# GraphTools v1.5（短期版・正史仕様）
# - 可変カラムCSV対応
# - id / x / y / summary / title / clusterId / argumentId は内部生成で補完
# - data30.csv / cluster30.csv を使用
# - /init, /dump, /health, /scatter, /hierarchy, /compare, /filter を提供

import csv
import json
import math
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

DB_PATH = "graph.db"
DATA_CSV = "data30.csv"
CLUSTER_CSV = "cluster30.csv"

app = FastAPI(title="GraphTools v1.5 Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# DB ユーティリティ
# =========================

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.executescript(
        """
        DROP TABLE IF EXISTS job_log;
        DROP TABLE IF EXISTS scatter_raw;
        DROP TABLE IF EXISTS scatter_cluster;
        DROP TABLE IF EXISTS scatter_dense;
        DROP TABLE IF EXISTS hierarchy;
        """
    )

    cur.execute(
        """
        CREATE TABLE job_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_name TEXT,
            condition TEXT,
            started_at TEXT,
            finished_at TEXT,
            status TEXT,
            is_sync INTEGER,
            input_json TEXT,
            output_json TEXT
        )
        """
    )

    for table in ["scatter_raw", "scatter_cluster", "scatter_dense"]:
        cur.execute(
            f"""
            CREATE TABLE {table} (
                id TEXT PRIMARY KEY,
                x REAL,
                y REAL,
                summary TEXT,
                title TEXT,
                cluster_id TEXT,
                argument_id TEXT
            )
            """
        )

    cur.execute(
        """
        CREATE TABLE hierarchy (
            id TEXT PRIMARY KEY,
            json TEXT
        )
        """
    )

    conn.commit()
    conn.close()


def log_job(
    job_name: str,
    condition: str,
    input_obj,
    output_obj,
    status: str = "success",
    is_sync: bool = True,
):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    input_json = json.dumps(input_obj, ensure_ascii=False)
    output_json = json.dumps(output_obj, ensure_ascii=False)
    cur.execute(
        """
        INSERT INTO job_log
        (job_name, condition, started_at, finished_at, status, is_sync, input_json, output_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            job_name,
            condition,
            now,
            now,
            status,
            1 if is_sync else 0,
            input_json,
            output_json,
        ),
    )
    conn.commit()
    conn.close()


# =========================
# モデル
# =========================

class ScatterPoint(BaseModel):
    id: str
    x: float
    y: float
    summary: str
    title: str
    clusterId: str
    argumentId: str


class HealthResponse(BaseModel):
    status: str
    db_exists: bool
    tables: List[str]


# =========================
# CSV ロード（可変カラム対応）
# =========================

def pick_text_column(row: dict, fieldnames: List[str]) -> str:
    """
    本文カラムを自動判定する。
    優先順位:
      1. fullOpinion
      2. text
      3. summary
      4. カラムが1つしかない場合 → それを本文とみなす
    """
    if "fullOpinion" in row and row["fullOpinion"]:
        return row["fullOpinion"]
    if "text" in row and row["text"]:
        return row["text"]
    if "summary" in row and row["summary"]:
        return row["summary"]
    if len(fieldnames) == 1:
        return row.get(fieldnames[0], "") or ""
    return ""


def safe_float(val, default=0.0):
    if val is None:
        return default
    s = str(val).strip()
    if s == "":
        return default
    try:
        return float(s)
    except ValueError:
        return default


def generate_xy(stable_id: str):
    """
    id から安定した擬似乱数的な x,y を生成。
    """
    hx = hash(stable_id + ":x")
    hy = hash(stable_id + ":y")
    x = (hx % 1000) / 100.0
    y = (hy % 1000) / 100.0
    return x, y


def load_data_csv():
    path = Path(DATA_CSV)
    if not path.exists():
        return {"loaded": False, "reason": f"{DATA_CSV} not found"}

    conn = get_conn()
    cur = conn.cursor()

    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    counter = 0
    for i, row in enumerate(rows):
        counter += 1
        # 内部用 id 生成
        stable_id = f"{int(datetime.utcnow().timestamp())}-{counter}"

        # 本文
        text = pick_text_column(row, reader.fieldnames or [])

        # summary / title 生成
        raw_summary = row.get("summary") or ""
        if raw_summary.strip():
            summary = raw_summary.strip()
        else:
            summary = text[:30] if text else f"意見 {counter}"

        title = summary[:10] if summary else f"タイトル {counter}"

        # x, y
        raw_x = row.get("x")
        raw_y = row.get("y")
        if raw_x is not None or raw_y is not None:
            x = safe_float(raw_x, 0.0)
            y = safe_float(raw_y, 0.0)
        else:
            x, y = generate_xy(stable_id)

        # clusterId / argumentId
        raw_cluster = row.get("cluster_id") or row.get("clusterId")
        if raw_cluster and str(raw_cluster).strip():
            cluster_id = str(raw_cluster).strip()
        else:
            cluster_id = f"C{counter % 5}"

        raw_argument = row.get("argumentId") or ""
        if raw_argument.strip():
            argument_id = raw_argument.strip()
        else:
            argument_id = f"{cluster_id}-{counter % 3}"

        # raw
        cur.execute(
            """
            INSERT OR REPLACE INTO scatter_raw
            (id, x, y, summary, title, cluster_id, argument_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (stable_id, x, y, summary, title, cluster_id, argument_id),
        )

        # cluster: x,y を別の位置に散らす（なんちゃってクラスタリング）
        cx, cy = generate_xy(stable_id + ":cluster")
        cur.execute(
            """
            INSERT OR REPLACE INTO scatter_cluster
            (id, x, y, summary, title, cluster_id, argument_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (stable_id, cx, cy, summary, title, cluster_id, argument_id),
        )

        # dense: 原点距離の逆数を使ったなんちゃって密度
        dist = math.sqrt(x * x + y * y) or 1.0
        dx = x
        dy = y
        cur.execute(
            """
            INSERT OR REPLACE INTO scatter_dense
            (id, x, y, summary, title, cluster_id, argument_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (stable_id, dx, dy, summary, title, cluster_id, argument_id),
        )

    conn.commit()
    conn.close()
    return {"loaded": True, "rows": len(rows)}


# =========================
# 階層CSV ロード（簡易版）
# =========================

def load_cluster_csv():
    """
    cluster30.csv を読み込み、アウトライン的な階層構造を JSON にして保存。
    短期版では「ファイル全体をラップして保存」する簡易実装。
    将来、公聴システムと同じ構造に拡張可能。
    """
    path = Path(CLUSTER_CSV)
    if not path.exists():
        return {"loaded": False, "reason": f"{CLUSTER_CSV} not found"}

    text = path.read_text(encoding="utf-8")
    obj = {"source": CLUSTER_CSV, "raw": text}

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR REPLACE INTO hierarchy (id, json)
        VALUES (?, ?)
        """,
        ("root", json.dumps(obj, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()
    return {"loaded": True}


# =========================
# API 実装
# =========================

@app.get("/health", response_model=HealthResponse)
def health():
    db_exists = Path(DB_PATH).exists()
    tables: List[str] = []
    if db_exists:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        conn.close()
    return HealthResponse(status="ok", db_exists=db_exists, tables=tables)


@app.post("/init")
def init():
    """
    明示的初期化:
      - DB 再作成
      - data30.csv / cluster30.csv 読み込み
      - job_log に記録
    """
    init_db()
    data_result = load_data_csv()
    cluster_result = load_cluster_csv()
    out = {"data": data_result, "cluster": cluster_result}
    log_job(
        job_name="init",
        condition="manual",
        input_obj={"csv": [DATA_CSV, CLUSTER_CSV]},
        output_obj=out,
        status="success",
        is_sync=True,
    )
    return out


@app.get("/dump")
def dump():
    """
    内部状態の簡易ダンプ:
      - 各テーブル件数
      - job_log 最新10件
    """
    if not Path(DB_PATH).exists():
        raise HTTPException(status_code=500, detail="DB not initialized")

    conn = get_conn()
    cur = conn.cursor()

    def count(table):
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        return cur.fetchone()[0]

    info = {
        "scatter_raw": count("scatter_raw"),
        "scatter_cluster": count("scatter_cluster"),
        "scatter_dense": count("scatter_dense"),
        "hierarchy": count("hierarchy"),
        "job_log": count("job_log"),
    }

    cur.execute(
        """
        SELECT id, job_name, condition, started_at, finished_at, status
        FROM job_log
        ORDER BY id DESC
        LIMIT 10
        """
    )
    jobs = [dict(r) for r in cur.fetchall()]
    conn.close()

    out = {"tables": info, "recent_jobs": jobs}
    log_job(
        job_name="dump",
        condition="manual",
        input_obj={},
        output_obj=out,
        status="success",
        is_sync=True,
    )
    return out


@app.get("/scatter", response_model=List[ScatterPoint])
def scatter(mode: str = Query("raw", regex="^(raw|cluster|dense)$")):
    """
    散布図データ:
      - mode=raw     → scatter_raw
      - mode=cluster → scatter_cluster
      - mode=dense   → scatter_dense
    レスポンスは配列そのもの（{count, data} ではない）。
    """
    if not Path(DB_PATH).exists():
        raise HTTPException(status_code=500, detail="DB not initialized")

    table = {
        "raw": "scatter_raw",
        "cluster": "scatter_cluster",
        "dense": "scatter_dense",
    }[mode]

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        f"""
        SELECT id, x, y, summary, title, cluster_id, argument_id
        FROM {table}
        """
    )
    rows = cur.fetchall()
    conn.close()

    result = [
        ScatterPoint(
            id=r["id"],
            x=r["x"],
            y=r["y"],
            summary=r["summary"],
            title=r["title"],
            clusterId=r["cluster_id"],
            argumentId=r["argument_id"],
        )
        for r in rows
    ]

    log_job(
        job_name="scatter",
        condition=f"mode={mode}",
        input_obj={"mode": mode},
        output_obj={"count": len(result)},
        status="success",
        is_sync=True,
    )
    return result


@app.get("/hierarchy")
def hierarchy(mode: str = Query("cluster")):
    """
    階層ビュー:
      - 短期版では cluster30.csv をラップした JSON を返す。
      - 将来、公聴システムと同じ構造に拡張可能。
    """
    if not Path(DB_PATH).exists():
        raise HTTPException(status_code=500, detail="DB not initialized")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT json FROM hierarchy WHERE id = ?", ("root",))
    row = cur.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="hierarchy not found")

    obj = json.loads(row["json"])
    log_job(
        job_name="hierarchy",
        condition=f"mode={mode}",
        input_obj={"mode": mode},
        output_obj={"source": obj.get("source")},
        status="success",
        is_sync=True,
    )
    return obj


@app.get("/compare")
def compare():
    """
    比較ビュー用簡易API:
      - 現状は cluster モードの scatter をそのまま返す。
      - 将来、複数条件比較に拡張可能。
    """
    data = scatter(mode="cluster")
    return {"mode": "cluster", "items": data}


@app.get("/filter")
def filter_api(
    clusterId: Optional[str] = None,
    argumentId: Optional[str] = None,
):
    """
    フィルタAPI:
      - clusterId / argumentId で scatter_raw を絞り込む。
    """
    if not Path(DB_PATH).exists():
        raise HTTPException(status_code=500, detail="DB not initialized")

    conn = get_conn()
    cur = conn.cursor()

    sql = """
        SELECT id, x, y, summary, title, cluster_id, argument_id
        FROM scatter_raw
        WHERE 1=1
    """
    params = []
    if clusterId:
        sql += " AND cluster_id = ?"
        params.append(clusterId)
    if argumentId:
        sql += " AND argument_id = ?"
        params.append(argumentId)

    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()

    result = [
        ScatterPoint(
            id=r["id"],
            x=r["x"],
            y=r["y"],
            summary=r["summary"],
            title=r["title"],
            clusterId=r["cluster_id"],
            argumentId=r["argument_id"],
        )
        for r in rows
    ]

    log_job(
        job_name="filter",
        condition=f"clusterId={clusterId}, argumentId={argumentId}",
        input_obj={"clusterId": clusterId, "argumentId": argumentId},
        output_obj={"count": len(result)},
        status="success",
        is_sync=True,
    )
    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8005)
