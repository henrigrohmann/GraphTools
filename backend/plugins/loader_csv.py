import csv
from pathlib import Path

# パスを動的に解決: backend/plugins から相対的に ../../data30.csv を探す
def _resolve_csv_path():
    """Resolve CSV path regardless of working directory."""
    here = Path(__file__).parent

    # 1. 同じディレクトリ
    if (here / "data30.csv").exists():
        return str(here / "data30.csv")

    # 2. 親ディレクトリ（backend/）
    if (here.parent / "data30.csv").exists():
        return str(here.parent / "data30.csv")

    # 3. 祖父ディレクトリ（workspace root）
    if (here.parent.parent / "data30.csv").exists():
        return str(here.parent.parent / "data30.csv")

    # 4. CWD
    if Path("data30.csv").exists():
        return "data30.csv"

    return "data30.csv"


CSV_PATH = _resolve_csv_path()

REQUIRED_COLUMNS = ["id", "cluster_id", "x", "y", "summary", "fullOpinion"]
OPTIONAL_COLUMNS = ["density"]


def load_csv(csv_path=None):
    """
    CSV を読み込み、以下の形式のリストを返す：
    (id, summary, fullOpinion, x, y, density)

    - 単一列 CSV → fullOpinion として扱う（新仕様）
    - density カラムがあれば読み込む
    - density が空欄を含む場合は「なんちゃって密度」
    - density カラムが無ければ「なんちゃって密度」
    - 未知カラムがあれば読み込みキャンセル
    - カラム数不一致なら読み込みキャンセル
    - 途中ヘッダー行は無視
    - 完全一致重複は除外
    """
    path = csv_path if csv_path else CSV_PATH

    rows = []
    seen = set()

    with open(path, encoding="utf-8") as f:
        reader = csv.reader(f)

        # -------------------------
        # 1. ヘッダー解析
        # -------------------------
        header = next(reader, None)
        if not header:
            raise ValueError("CSV が空です")

        header = [h.strip() for h in header]

        # ------------------------------------------------------------
        # ★ 単一列モード：ヘッダーが1つだけ → fullOpinion として扱う
        # ------------------------------------------------------------
        if len(header) == 1:
            # ファイル先頭に戻す
            f.seek(0)
            reader = csv.reader(f)
            next(reader, None)  # skip header

            for i, row in enumerate(reader):
                if not row or not row[0].strip():
                    continue

                full = row[0].strip()

                record = (
                    str(i),        # id
                    full[:40],     # summary
                    full,          # fullOpinion
                    None,          # x
                    None,          # y
                    None,          # density（後で付与）
                )

                if record in seen:
                    continue
                seen.add(record)
                rows.append(record)

            # density を後で付与
            return attach_fake_density(rows)

        # ------------------------------------------------------------
        # ★ 多列モード（従来仕様）
        # ------------------------------------------------------------

        # 必須カラムチェック
        for col in REQUIRED_COLUMNS:
            if col not in header:
                raise ValueError(f"必須カラムがありません: {col}")

        has_density = "density" in header

        allowed = set(REQUIRED_COLUMNS + OPTIONAL_COLUMNS)
        for col in header:
            if col not in allowed:
                raise ValueError(f"未知のカラムがあります: {col}")

        idx = {col: header.index(col) for col in header}
        density_missing = False

        # -------------------------
        # 2. 行ごとの読み込み
        # -------------------------
        for row in reader:
            if not row or all(c.strip() == "" for c in row):
                continue

            if row[0].strip().lower() == "id":
                continue

            if len(row) != len(header):
                raise ValueError(f"カラム数が一致しません: {row}")

            id_ = row[idx["id"]].strip()
            summary = row[idx["summary"]].strip()
            fullOpinion = row[idx["fullOpinion"]].strip()

            x_raw = row[idx["x"]].strip()
            y_raw = row[idx["y"]].strip()

            try:
                x = float(x_raw) if x_raw else None
            except:
                raise ValueError(f"x の値が不正です: {x_raw}")

            try:
                y = float(y_raw) if y_raw else None:
                    ...
            except:
                raise ValueError(f"y の値が不正です: {y_raw}")

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

            if record in seen:
                continue
            seen.add(record)

            rows.append(record)

    # -------------------------
    # 3. density の補完
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

    coords = [(r[3], r[4]) for r in rows]

    densities = []
    R = 0.15

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

    max_d = max(densities) if densities else 1
    if max_d == 0:
        norm = [0.0 for _ in densities]
    else:
        norm = [d / max_d for d in densities]

    new_rows = []
    for (id_, summary, fullOpinion, x, y, _), d in zip(rows, norm):
        new_rows.append((id_, summary, fullOpinion, x, y, d))

    return new_rows
