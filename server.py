from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import pandas as pd
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

    # 既存DBがあれば削除して再生成（安全のため）
    if os.path.exists(DB_PATH):
        log("Existing DB found. Removing it for clean init.")
        os.remove(DB_PATH)

    # CSV 読み込み
    try:
        log("Reading CSV...")
        df = pd.read_csv(CSV_PATH)
        log(f"CSV loaded. Rows = {len(df)}")
        log(f"CSV columns = {list(df.columns)}")
    except Exception as e:
        log("ERROR: CSV 読み込みに失敗")
        log(traceback.format_exc())
        return

    # points 生成
    try:
        points = []
        for _, row in df.iterrows():
            points.append({
                "id": str(row["id"]),
                "cluster": str(row["cluster_id"]),
                "x": float(row["x"]),
                "y": float(row["y"]),
                "text": str(row["text"])
            })
        log(f"Points parsed: {len(points)}")
    except Exception as e:
        log("ERROR: points 生成に失敗")
        log(traceback.format_exc())
        return

    # clusters 生成
    try:
        cluster_ids = sorted(df["cluster_id"].unique())
        clusters = [{"id": str(cid), "parent": None, "name": str(cid)} for cid in cluster_ids]
        log(f"Clusters parsed: {len(clusters)}")
    except Exception as e:
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
    except Exception as e:
        log("ERROR: DB 書き込みに失敗")
        log(traceback.format_exc())
        return

    log("=== init_db() end ===")

# 初期化実行
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

    except Exception as e:
        log("ERROR: scatter_data API failed")
        log(traceback.format_exc())
        return {"error": "API failed"}
