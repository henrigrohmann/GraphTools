# server.py
#
# GraphTool v1.5 正史準拠バックエンド
# - FastAPI + SQLite
# - data30.csv / cluster30.csv を読み込み
# - /scatter, /hierarchy, /init, /dump, /health, /compare, /filter
# - job_log にジョブ実行履歴を永続化（明示的な /init まで保持）

import json
import math
import os
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

app = FastAPI(title="GraphTool v1.5 Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- DB ユーティリティ ----------

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # 既存テーブル削除
    cur.executescript(
        """
        DROP TABLE IF EXISTS job_log;
        DROP TABLE IF EXISTS scatter_raw;
        DROP TABLE IF EXISTS scatter_cluster;
        DROP TABLE IF EXISTS scatter_dense;
        DROP TABLE IF EXISTS hierarchy;
        """
    )

    # job_log: ジョブ履歴
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

    # scatter_*: 散布図用データ
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

    # hierarchy: 階層構造（JSON そのまま）
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


# ---------- CSV ロード & なんちゃって生成 ----------

def load_data_csv():
    """
    data30.csv を読み込み、scatter_raw / scatter_cluster / scatter_dense に投入する。
    想定カラム:
      id, x, y, summary, title, clusterId, argumentId
    summary / title / clusterId / argumentId が空なら、なんちゃって生成。
    """
    path = Path(DATA_CSV)
    if not path.exists():
        return {"loaded": False, "reason": f"{DATA_CSV} not found"}

    import csv

    conn = get_conn()
    cur = conn.cursor()

    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    def ensure(val, fallback):
        return val if val not in (None, "", "null") else fallback

    for i, row in enumerate(rows):
        rid = ensure(row.get("id"), f"row-{i+1}")
        x = float(row.get("x") or 0.0)
        y = float(row.get("y") or 0.0)
        summary = ensure(row.get("summary"), f"サマリー {i+1}")
        title = ensure(row.get("title"), f"タイトル {i+1}")
        cluster_id = ensure(row.get("clusterId"), f"C{i%5}")
        argument_id = ensure(row.get("argumentId"), f"{cluster_id}-{i%3}")

        # raw
        cur.execute(
            """
            INSERT OR REPLACE INTO scatter_raw
            (id, x, y, summary, title, cluster_id, argument_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (rid, x, y, summary, title, cluster_id, argument_id),
        )

        # random: 意味空間に一様に散らばるランダム値
        rx = (hash(f"{rid}-x") % 1000) / 100.0
        ry = (hash(f"{rid}-y") % 1000) / 100.0
        cur.execute(
            """
            INSERT OR REPLACE INTO scatter_cluster
            (id, x, y, summary, title, cluster_id, argument_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (rid, rx, ry, summary, title, cluster_id, argument_id),
        )

        # dense: なんちゃって密度（原点からの距離の逆数）
        dist = math.sqrt(x * x + y * y) or 1.0
        dx = x
        dy = y
        cur.execute(
            """
            INSERT OR REPLACE INTO scatter_dense
            (id, x, y, summary, title, cluster_id, argument_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (rid, dx, dy, summary, title, cluster_id, argument_id),
        )

    conn.commit()
    conn.close()
    return {"loaded": True, "rows": len(rows)}


def load_cluster_csv():
    """
    cluster30.csv を読み込み、階層定義を JSON として hierarchy テーブルに保存する。
    ここでは簡易に「ファイル全体を JSON 文字列として 1 レコードに格納」する。
    将来、公聴システムと同じオブジェクト構造に拡張可能。
    """
    path = Path(CLUSTER_CSV)
    if not path.exists():
        return {"loaded": False, "reason": f"{CLUSTER_CSV} not found"}

    text = path.read_text(encoding="utf-8")

    # ここでは「生テキスト」をそのまま JSON として扱うラッパーを作る
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


# ---------- Pydantic モデル ----------

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


# ---------- API 実装 ----------

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
    明示的な初期化。
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
    内部状態の簡易ダンプ。
    - 各テーブルの件数
    - job_log の最新 10 件
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
    散布図データを返す。
    - mode=raw     → scatter_raw
    - mode=cluster → scatter_cluster
    - mode=dense   → scatter_dense
    レスポンスは「配列そのもの」を返す（{count, data} ではない）。
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
    階層ビュー。
    現状は cluster30.csv を JSON ラップして保存したものをそのまま返す。
    将来、公聴システムと同じオブジェクト構造に拡張可能。
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
    比較ビュー用の簡易 API。
    現状は cluster モードの scatter をそのまま返す。
    将来、複数条件比較に拡張可能。
    """
    data = scatter(mode="cluster")
    return {"mode": "cluster", "items": data}


@app.get("/filter")
def filter_api(
    clusterId: Optional[str] = None,
    argumentId: Optional[str] = None,
):
    """
    フィルタ API。
    clusterId / argumentId で scatter_raw を絞り込む。
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
