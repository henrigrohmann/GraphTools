import sqlite3
from pathlib import Path
import json
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "opinions.db"

# 既存
TABLE_OPINIONS_RAW = "opinions_raw"
TABLE_OPINIONS_RANDOM = "opinions_random"
TABLE_OPINIONS_CLUSTERED = "opinions_clustered"
TABLE_OPINIONS_DENSE = "opinions_dense"
TABLE_JOBS = "jobs"

# 新規（階層データ）
TABLE_HIERARCHY_EXTERNAL = "hierarchy_external"
TABLE_HIERARCHY_CLUSTER = "hierarchy_cluster"
TABLE_HIERARCHY_DENSE = "hierarchy_dense"


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_tables():
    conn = _get_conn()
    cur = conn.cursor()

    # --- 既存テーブル ---
    for tbl in [
        TABLE_OPINIONS_RAW,
        TABLE_OPINIONS_RANDOM,
        TABLE_OPINIONS_CLUSTERED,
        TABLE_OPINIONS_DENSE,
    ]:
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {tbl} (
                id TEXT,
                cluster_id TEXT,
                x REAL,
                y REAL,
                summary TEXT,
                fullOpinion TEXT,
                density REAL
            )
            """
        )

    # --- JOB テーブル ---
    cur.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {TABLE_JOBS} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payload TEXT
        )
        """
    )

    # --- 階層テーブル（3種類） ---
    for tbl in [
        TABLE_HIERARCHY_EXTERNAL,
        TABLE_HIERARCHY_CLUSTER,
        TABLE_HIERARCHY_DENSE,
    ]:
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {tbl} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clusterList TEXT,
                argumentList TEXT,
                created_at TEXT
            )
            """
        )

    conn.commit()
    conn.close()


_init_tables()


# -----------------------------
# 意見テーブル書き込み
# -----------------------------
def write_opinions(table_name, opinions):
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(f"DELETE FROM {table_name}")

    for op in opinions:
        cur.execute(
            f"""
            INSERT INTO {table_name}
            (id, cluster_id, x, y, summary, fullOpinion, density)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                op.get("id"),
                op.get("cluster_id", ""),
                op.get("x"),
                op.get("y"),
                op.get("summary"),
                op.get("fullOpinion"),
                op.get("density"),
            ),
        )

    conn.commit()
    conn.close()


def read_opinions(table_name):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table_name}")
    rows = cur.fetchall()
    conn.close()

    return [dict(r) for r in rows]


# -----------------------------
# JOB ログ
# -----------------------------
def log_job(payload: dict):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        f"INSERT INTO {TABLE_JOBS} (payload) VALUES (?)",
        (json.dumps(payload, ensure_ascii=False),),
    )
    conn.commit()
    conn.close()


def read_jobs():
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(f"SELECT id, payload FROM {TABLE_JOBS} ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()

    result = []
    for r in rows:
        try:
            p = json.loads(r["payload"])
        except Exception:
            p = {"raw": r["payload"]}
        p["_id"] = r["id"]
        result.append(p)
    return result


# -----------------------------
# 階層データ
# -----------------------------
def delete_hierarchy(mode: str):
    """
    mode = external | cluster | dense | all
    """
    conn = _get_conn()
    cur = conn.cursor()

    if mode == "external":
        cur.execute(f"DELETE FROM {TABLE_HIERARCHY_EXTERNAL}")
    elif mode == "cluster":
        cur.execute(f"DELETE FROM {TABLE_HIERARCHY_CLUSTER}")
    elif mode == "dense":
        cur.execute(f"DELETE FROM {TABLE_HIERARCHY_DENSE}")
    elif mode == "all":
        cur.execute(f"DELETE FROM {TABLE_HIERARCHY_EXTERNAL}")
        cur.execute(f"DELETE FROM {TABLE_HIERARCHY_CLUSTER}")
        cur.execute(f"DELETE FROM {TABLE_HIERARCHY_DENSE}")

    conn.commit()
    conn.close()


def write_hierarchy(table_name, clusterList, argumentList):
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(f"DELETE FROM {table_name}")

    cur.execute(
        f"""
        INSERT INTO {table_name}
        (clusterList, argumentList, created_at)
        VALUES (?, ?, ?)
        """,
        (
            json.dumps(clusterList, ensure_ascii=False),
            json.dumps(argumentList, ensure_ascii=False),
            datetime.now().isoformat(),
        ),
    )

    conn.commit()
    conn.close()


def read_hierarchy(table_name):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "clusterList": json.loads(row["clusterList"]),
        "argumentList": json.loads(row["argumentList"]),
        "created_at": row["created_at"],
    }
