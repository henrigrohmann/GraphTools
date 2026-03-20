import sqlite3
import json
from datetime import datetime

DB_PATH = "data.db"

TABLE_OPINIONS_RAW = "opinions_raw"
TABLE_OPINIONS_RANDOM = "opinions_random"
TABLE_OPINIONS_CLUSTERED = "opinions_clustered"
TABLE_JOBS_LOG = "jobs_log"


def _get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    """
    DB と 4 テーブル（raw / random / clustered / jobs_log）を初期化する。
    既存の DB があればそのまま使い、テーブルが無ければ作る。
    """
    conn = _get_conn()
    cur = conn.cursor()

    # 共通スキーマ: id / created_at / is_debug / payload_json
    def create_table(name: str):
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT,
                is_debug INTEGER,
                payload_json TEXT
            )
            """
        )

    create_table(TABLE_OPINIONS_RAW)
    create_table(TABLE_OPINIONS_RANDOM)
    create_table(TABLE_OPINIONS_CLUSTERED)
    create_table(TABLE_JOBS_LOG)

    conn.commit()
    conn.close()


def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


def reset_opinions_tables():
    """
    opinions_raw / opinions_random / opinions_clustered の3テーブルを初期化する。
    jobs_log は残す。
    """
    init_db()
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(f"DELETE FROM {TABLE_OPINIONS_RAW}")
    cur.execute(f"DELETE FROM {TABLE_OPINIONS_RANDOM}")
    cur.execute(f"DELETE FROM {TABLE_OPINIONS_CLUSTERED}")

    conn.commit()
    conn.close()


def write_opinions(table_name: str, payloads: list[dict], is_debug: bool = True):
    """
    意見データを指定テーブルにまとめて書き込む。
    payloads: [{...}, {...}, ...]  ← 1件がそのまま JSON になる

    - DB 内に完全一致のレコードがある場合はスキップする
    - 初期化しない限り append モード
    """
    init_db()
    conn = _get_conn()
    cur = conn.cursor()

    created_at = _now_iso()
    debug_flag = 1 if is_debug else 0

    # 既存レコードを読み込み、重複チェック用セットを作る
    cur.execute(f"SELECT payload_json FROM {table_name}")
    existing_rows = cur.fetchall()

    existing_set = set()
    for (payload_json,) in existing_rows:
        try:
            existing_set.add(payload_json)
        except Exception:
            continue

    # 新規 payload を DB に書き込む（完全一致重複は除外）
    for payload in payloads:
        payload_str = json.dumps(payload, ensure_ascii=False)

        if payload_str in existing_set:
            continue  # 完全一致の重複 → スキップ

        cur.execute(
            f"""
            INSERT INTO {table_name} (created_at, is_debug, payload_json)
            VALUES (?, ?, ?)
            """,
            (created_at, debug_flag, payload_str),
        )

        existing_set.add(payload_str)

    conn.commit()
    conn.close()


def read_opinions(table_name: str) -> list[dict]:
    """
    指定テーブルから payload_json を読み出して、
    Python の dict のリストとして返す。
    """
    init_db()
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        f"""
        SELECT payload_json
        FROM {table_name}
        ORDER BY id ASC
        """
    )
    rows = cur.fetchall()
    conn.close()

    result = []
    for (payload_json,) in rows:
        try:
            result.append(json.loads(payload_json))
        except Exception:
            continue
    return result


def log_job(job_payload: dict, is_debug: bool = True):
    """
    JOB 実行ログを jobs_log テーブルに 1 件書き込む。
    job_payload はそのまま JSON として保存される。
    """
    init_db()
    conn = _get_conn()
    cur = conn.cursor()

    created_at = _now_iso()
    debug_flag = 1 if is_debug else 0

    cur.execute(
        f"""
        INSERT INTO {TABLE_JOBS_LOG} (created_at, is_debug, payload_json)
        VALUES (?, ?, ?)
        """,
        (created_at, debug_flag, json.dumps(job_payload, ensure_ascii=False)),
    )

    conn.commit()
    conn.close()


def read_jobs() -> list[dict]:
    """
    jobs_log テーブルから JOB ログを読み出す。
    """
    init_db()
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        f"""
        SELECT payload_json
        FROM {TABLE_JOBS_LOG}
        ORDER BY id DESC
        """
    )
    rows = cur.fetchall()
    conn.close()

    result = []
    for (payload_json,) in rows:
        try:
            result.append(json.loads(payload_json))
        except Exception:
            continue
    return result
