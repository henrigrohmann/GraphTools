import sqlite3
import os

DB_PATH = "data.db"


def write_db(rows, labels, xy):
    """
    rows:   [(id, summary, fullOpinion), ...]
    labels: [label, ...]  (0..k-1 or -1)
    xy:     [(x, y), ...]
    """
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE opinions (
            id TEXT PRIMARY KEY,
            cluster_id TEXT,
            x REAL,
            y REAL,
            summary TEXT,
            fullOpinion TEXT
        )
        """
    )

    for (id_, summary, fullOpinion), label, (x, y) in zip(rows, labels, xy):
        if label == -1:
            cluster_name = ""
        else:
            cluster_name = ["A", "B", "C"][label % 3]

        cur.execute(
            """
            INSERT INTO opinions (id, cluster_id, x, y, summary, fullOpinion)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (id_, cluster_name, x, y, summary, fullOpinion),
        )

    conn.commit()
    conn.close()


def read_scatter():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, cluster_id, x, y, summary, fullOpinion FROM opinions")
    rows = cur.fetchall()
    conn.close()

    data = []
    for r in rows:
        data.append(
            {
                "id": r[0],
                "cluster_id": r[1],
                "x": r[2],
                "y": r[3],
                "summary": r[4],
                "fullOpinion": r[5],
            }
        )
    return {"count": len(data), "data": data}
