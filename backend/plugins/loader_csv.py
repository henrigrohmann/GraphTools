import csv

CSV_PATH = "data30.csv"

REQUIRED_COLUMNS = ["id", "cluster_id", "x", "y", "summary", "fullOpinion"]
OPTIONAL_COLUMNS = ["density"]


def load_csv():
    """
    CSV を読み込み、以下の形式のリストを返す：
    (id, summary, fullOpinion, x, y, density)

    - density カラムがあれば読み込む
    - density が空欄を含む場合は「なんちゃって密度」に切り替え
    - density カラムが無ければ「なんちゃって密度」
    - 未知カラムがあれば読み込みキャンセル
    - カラム数不一致なら読み込みキャンセル
    - 途中ヘッダー行は無視
    - 完全一致重複は除外
    """

    rows = []
    seen = set()

    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.reader(f)

        # -------------------------
        # 1. ヘッダー解析
        # -------------------------
        header = next(reader, None)
        if not header:
            raise ValueError("CSV が空です")

        header = [h.strip() for h in header]

        # 必須カラムが揃っているか
        for col in REQUIRED_COLUMNS:
            if col not in header:
                raise ValueError(f"必須カラムがありません: {col}")

        # density カラムの有無
        has_density = "density" in header

        # 未知カラムの検出
        allowed = set(REQUIRED_COLUMNS + OPTIONAL_COLUMNS)
        for col in header:
            if col not in allowed:
                raise ValueError(f"未知のカラムがあります: {col}")

        # カラム位置を取得
        idx = {col: header.index(col) for col in header}

        # density の空欄検出フラグ
        density_missing = False

        # -------------------------
        # 2. 行ごとの読み込み
        # -------------------------
        for row in reader:
            # 空行
            if not row or all(c.strip() == "" for c in row):
                continue

            # 途中に混ざるヘッダー行
            if row[0].strip().lower() == "id":
                continue

            # カラム数不一致
            if len(row) != len(header):
                raise ValueError(f"カラム数が一致しません: {row}")

            # 必須カラム取り出し
            id_ = row[idx["id"]].strip()
            summary = row[idx["summary"]].strip()
            fullOpinion = row[idx["fullOpinion"]].strip()

            # x, y
            x_raw = row[idx["x"]].strip()
            y_raw = row[idx["y"]].strip()

            try:
                x = float(x_raw) if x_raw else None
            except:
                raise ValueError(f"x の値が不正です: {x_raw}")

            try:
                y = float(y_raw) if y_raw else None
            except:
                raise ValueError(f"y の値が不正です: {y_raw}")

            # density
            if has_density:
                d_raw = row[idx["density"]].strip()
                if d_raw == "":
                    density_missing = True
                    density = None
                else:
                    try:
                        density = float(d_raw)
                    except:
                        raise ValueError(f"density の値が不正です: {d_raw}")
            else:
                density = None

            record = (id_, summary, fullOpinion, x, y, density)

            # 重複除外
            if record in seen:
                continue
            seen.add(record)

            rows.append(record)

    # -------------------------
    # 3. density の補完（なんちゃって密度）
    # -------------------------
    if (not has_density) or density_missing:
        rows = attach_fake_density(rows)

    return rows


def attach_fake_density(rows):
    """
    なんちゃって密度を計算して付与する。
    非常に軽量な近傍カウント方式。
    """
    if not rows:
        return rows

    # x,y が None の場合はランダム座標後に計算される前提
    coords = [(r[3], r[4]) for r in rows]

    densities = []
    R = 0.15  # 近傍半径（軽量固定値）

    for i, (x1, y1) in enumerate(coords):
        if x1 is None or y1 is None:
            densities.append(0.0)
            continue

        count = 0
        for j, (x2, y2) in enumerate(coords):
            if i == j:
                continue
            if x2 is None or y2 is None:
                continue
            dx = x1 - x2
            dy = y1 - y2
            if dx * dx + dy * dy <= R * R:
                count += 1

        densities.append(count)

    # 正規化
    max_d = max(densities) if densities else 1
    if max_d == 0:
        norm = [0.0 for _ in densities]
    else:
        norm = [d / max_d for d in densities]

    # density を付与した新しい rows を返す
    new_rows = []
    for (id_, summary, fullOpinion, x, y, _), d in zip(rows, norm):
        new_rows.append((id_, summary, fullOpinion, x, y, d))

    return new_rows
