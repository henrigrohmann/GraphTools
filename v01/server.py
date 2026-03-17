from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import csv
import os
import traceback

DB_PATH = "graph.db"
CSV_PATH = "data30.csv"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def log(msg):
    print(f"[LOG] {msg}")

def init_db():
    log("=== init_db() start ===")
    log(f"CWD = {os.getcwd()}")
    log(f"CSV_PATH = {CSV_PATH}")
    log(f"DB_PATH = {DB_PATH}")

    # 既存DB削除
    if os.path.exists(DB_PATH):
        log("Existing DB found. Removing it.")
        os.remove(DB_PATH)

    # CSV 読み込み
    try:
        log("Reading CSV via csv.reader...")
        with open(CSV_PATH, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        log(f"CSV loaded. Rows = {len(rows)}")
        log(f"CSV columns = {reader.fieldnames}")
    except Exception:
        log("ERROR: CSV 読み込みに失敗")
        log(traceback.format_exc())
        return

    # points 生成
    try:
        points = []
        for row in rows:
            points.append({
                "id": row["id"],
                "cluster": row["cluster_id"],
                "x": float(row["x"]),
                "y": float(row["y"]),
                "text": row["text"]
            })
        log(f"Points parsed: {len(points)}")
    except Exception:
        log("ERROR: points 生成に失敗")
        log(traceback.format_exc())
        return

    # clusters 生成
    try:
        cluster_ids = sorted(set(row["cluster_id"] for row in rows))
        clusters = [{"id": cid, "parent": None, "name": cid} for cid in cluster_ids]
        log(f"Clusters parsed: {len(clusters)}")
    except Exception:
        log("ERROR: clusters 生成に失敗")
        log(traceback.format_exc())
        return

    # DB 書き込み
    try:
        log("Creating DB and tables...")
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute("CREATE TABLE clusters (id TEXT, parent TEXT, name TEXT)")
        cur.execute("CREATE TABLE points (id TEXT, cluster TEXT, x REAL, y REAL, text TEXT)")

        log("Inserting clusters...")
        cur.executemany("INSERT INTO clusters VALUES (:id, :parent, :name)", clusters)

        log("Inserting points...")
        cur.executemany("INSERT INTO points VALUES (:id, :cluster, :x, :y, :text)", points)

        conn.commit()
        conn.close()
        log("DB initialization completed successfully.")
    except Exception:
        log("ERROR: DB 書き込みに失敗")
        log(traceback.format_exc())
        return

    log("=== init_db() end ===")

# 初期化
init_db()

@app.get("/scatter_data")
def scatter_data():
    log("API /scatter_data called")

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        clusters = [
            {"id": r[0], "parent": r[1], "name": r[2]}
            for r in cur.execute("SELECT id, parent, name FROM clusters")
        ]

        points = [
            {"id": r[0], "cluster": r[1], "x": r[2], "y": r[3], "text": r[4]}
            for r in cur.execute("SELECT id, cluster, x, y, text FROM points")
        ]

        conn.close()

        log(f"Returned clusters={len(clusters)}, points={len(points)}")
        return {"clusters": clusters, "points": points}

    except Exception:
        log("ERROR: scatter_data API failed")
        log(traceback.format_exc())
        return {"error": "API failed"}
