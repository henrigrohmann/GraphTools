import csv
import sqlite3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

DB_PATH = "data.db"
CSV_PATH = "data30.csv"

app = FastAPI()

# CORS（フロントからのアクセス許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# DB 初期化
# -----------------------------
def init_db():
    if os.path.exists(DB_PATH):
        print("[INFO] DB already exists. Skipping init.")
        return

    print("[INFO] Initializing DB...")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE opinions (
            id TEXT PRIMARY KEY,
            cluster_id TEXT,
            x REAL,
            y REAL,
            summary TEXT,
            fullOpinion TEXT
        )
    """)

    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # header skip

        for row in reader:
            id_, cluster_id, x, y, summary, *rest = row
            fullOpinion = ",".join(rest)

            cur.execute("""
                INSERT INTO opinions (id, cluster_id, x, y, summary, fullOpinion)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (id_, cluster_id, float(x), float(y), summary, fullOpinion))

    conn.commit()
    conn.close()
    print("[INFO] DB initialized.")

# -----------------------------
# API: scatter 用データ
# -----------------------------
@app.get("/scatter")
def get_scatter():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT id, cluster_id, x, y, summary, fullOpinion FROM opinions")
    rows = cur.fetchall()
    conn.close()

    data = []
    for r in rows:
        data.append({
            "id": r[0],
            "cluster_id": r[1],
            "x": r[2],
            "y": r[3],
            "summary": r[4],
            "fullOpinion": r[5]
        })

    return {"count": len(data), "data": data}

# -----------------------------
# 起動
# -----------------------------
if __name__ == "__main__":
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8000)
