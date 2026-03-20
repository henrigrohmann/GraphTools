import sqlite3
from pathlib import Path
import json

DB_PATH = Path(__file__).parent.parent / "opinions.db"

TABLE_OPINIONS_RAW = "opinions_raw"
TABLE_OPINIONS_RANDOM = "opinions_random"
TABLE_OPINIONS_CLUSTERED = "opinions_clustered"
TABLE_OPINIONS_DENSE = "opinions_dense"
TABLE_JOBS = "jobs"


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_tables():
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {TABLE_OPINIONS_RAW} (
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

    cur.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {TABLE_OPINIONS_RANDOM} (
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

    cur.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {TABLE_OPINIONS_CLUSTERED} (
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

    cur.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {TABLE_OPINIONS_DENSE} (
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

    cur.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {TABLE_JOBS} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payload TEXT
        )
        """
    )

    conn.commit()
    conn.close()


_init_tables()


def write_opinions(table_name, opinions):
    """
    opinions: list of dict
      {
        "id": str,
        "cluster_id": str,
        "x": float,
        "y": float,
        "summary": str,
        "fullOpinion": str,
        "density": float | None (optional)
      }
    """
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
    cur.execute(f"SELECT id, cluster_id, x, y, summary, fullOpinion, density FROM {table_name}")
    rows = cur.fetchall()
    conn.close()

    result = []
    for r in rows:
        result.append(
            {
                "id": r["id"],
                "cluster_id": r["cluster_id"],
                "x": r["x"],
                "y": r["y"],
                "summary": r["summary"],
                "fullOpinion": r["fullOpinion"],
                "density": r["density"],
            }
        )
    return result


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
