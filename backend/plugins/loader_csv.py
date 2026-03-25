import csv
from pathlib import Path

# パスを動的に解決: backend/plugins から相対的に ../../data30.csv を探す
def _resolve_csv_path():
    here = Path(__file__).parent

    if (here / "data30.csv").exists():
        return str(here / "data30.csv")

    if (here.parent / "data30.csv").exists():
        return str(here.parent / "data30.csv")

    if (here.parent.parent / "data30.csv").exists():
        return str(here.parent.parent / "data30.csv")

    if Path("data30.csv").exists():
        return "data30.csv"

    return "data30.csv"


CSV_PATH = _resolve_csv_path()

REQUIRED_COLUMNS = ["id", "cluster_id", "x", "y", "summary", "fullOpinion"]
OPTIONAL_COLUMNS = ["density"]


def attach_fake_density(rows):
    """
    なんちゃって密度を計算して付与する。
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


def load_csv(csv_path=None):
    """
    CSV を読み込み、以下の形式のリストを返す：
    (id, summary, fullOpinion, x, y, density)
    """
    path = csv_path if csv_path else CSV_PATH

    rows = []
    seen = set()

    with open(path, encoding="utf-8") as f:
        reader = csv.reader(f)

        header = next(reader, None)
        if not header:
            raise ValueError("CSV が空です")

        header = [h.strip() for h in header]

        # ------------------------------------------------------------
        # ★ 単一列モード
        # ------------------------------------------------------------
        if len(header) == 1:
            f.seek(0)
            reader = csv.reader(f)
            next(reader, None)

            for i, row in enumerate(reader):
                if not row or not row[0].strip():
                    continue

                full = row[0].strip()

                record = (
                    str(i),
                    full[:40],
                    full,
                    None,
                    None,
                    None,
                )

                if record in seen:
                    continue
                seen.add(record)
                rows.append(record)

            return attach_fake_density(rows)

        # ------------------------------------------------------------
        # ★ 多列モード
        # ------------------------------------------------------------
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
                y = float(y_raw) if y_raw else None
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

    if (not has_density) or density_missing:
        rows = attach_fake_density(rows)

    return rows
