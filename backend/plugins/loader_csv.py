import csv

CSV_PATH = "data30.csv"


def load_csv():
    """
    CSV を読み込み、以下の形式のリストを返す：
    (id, summary, fullOpinion, x, y)

    CSV フォーマット想定：
    id,cluster_id,x,y,summary,fullOpinion

    x,y が空欄の場合は None を返す。
    """
    rows = []
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip first header

        for row in reader:
            if len(row) < 6:
                continue

            # データ途中に同じヘッダー行が混在しているケースを除外する
            if row[0].strip().lower() == "id" and row[2].strip().lower() == "x":
                continue

            # CSV の列構造に合わせて取り出す
            id_ = row[0]
            _cluster = row[1]

            # x, y は空欄なら None
            x_raw = row[2].strip()
            y_raw = row[3].strip()
            x = float(x_raw) if x_raw else None
            y = float(y_raw) if y_raw else None

            summary = row[4]
            fullOpinion = ",".join(row[5:])  # カンマを含む可能性に対応

            rows.append((id_, summary, fullOpinion, x, y))

    return rows
