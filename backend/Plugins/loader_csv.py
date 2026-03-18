import csv

CSV_PATH = "data30.csv"


def load_csv():
    """
    data30.csv を読み込み、
    (id, summary, fullOpinion) のリストを返す。
    CSV フォーマット:
    id,cluster_id,x,y,summary,fullOpinion
    """
    rows = []
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # header skip
        for row in reader:
            id_, cluster_id, x, y, summary, *rest = row
            fullOpinion = ",".join(rest)
            rows.append((id_, summary, fullOpinion))
    return rows
