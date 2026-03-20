"""
階層CSV（cluster30.csv）読み込みロジック
※ 現時点ではコメントアウトしておくが、将来 /hierarchy で利用する
"""

import csv
import time
from pathlib import Path


def _resolve_cluster_csv_path():
    here = Path(__file__).parent
    candidates = [
        here / "cluster30.csv",
        here.parent / "cluster30.csv",
        here.parent.parent / "cluster30.csv",
        Path("cluster30.csv"),
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return None


# ---------------------------------------------------------
# コメントアウト：階層CSV読み込みロジック
# ---------------------------------------------------------
"""
def load_hierarchy_csv():
    path = _resolve_cluster_csv_path()
    if not path:
        return None  # CSV が無い

    rows = []
    with open(path, encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if not any(row):
                continue
            rows.append(row)

    # 空欄継承
    last_values = [""] * len(rows[0])
    filled = []
    for row in rows:
        new_row = []
        for i, cell in enumerate(row):
            cell = cell.strip()
            if cell:
                last_values[i] = cell
            new_row.append(last_values[i])
        filled.append(new_row)

    # 整理番号付与
    timestamp = int(time.time() * 1000)
    argumentList = []
    clusterList = []

    # ツリー構造生成
    # 例:
    # col0 = 親
    # col1 = 子
    # col2 = 孫
    # ...
    # 整理番号をキーにして階層構造を作る

    id_counter = 0
    node_map = {}  # 意見本文 → 整理番号

    for row in filled:
        for depth, text in enumerate(row):
            if not text:
                continue

            if text not in node_map:
                uid = f"{timestamp}-{id_counter:04d}"
                id_counter += 1
                node_map[text] = uid

                argumentList.append({
                    "id": uid,
                    "summary": "",
                    "fullOpinion": text,
                    "children": []
                })

            # 親子関係の構築
            if depth > 0:
                parent_text = row[depth - 1]
                if parent_text:
                    parent_id = node_map[parent_text]
                    child_id = node_map[text]

                    # 親の children に追加
                    for a in argumentList:
                        if a["id"] == parent_id:
                            if child_id not in a["children"]:
                                a["children"].append(child_id)

    # clusterList は最上位ノードのみ
    top_nodes = []
    for row in filled:
        top_text = row[0]
        if top_text:
            uid = node_map[top_text]
            if uid not in top_nodes:
                top_nodes.append(uid)

    clusterList = [{"id": uid, "label": "", "summary": "", "memberIds": []}
                   for uid in top_nodes]

    return {
        "clusterList": clusterList,
        "argumentList": argumentList
    }
"""
