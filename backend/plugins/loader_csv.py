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
       
