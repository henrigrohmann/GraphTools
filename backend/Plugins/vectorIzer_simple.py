def text_to_vector(text: str):
    length = len(text)
    if length == 0:
        length = 1

    num_punct = sum(1 for c in text if c in "。、.,!?！？")
    num_hira = sum(1 for c in text if "ぁ" <= c <= "ん")
    num_kata = sum(1 for c in text if "ァ" <= c <= "ン")
    num_digit = sum(1 for c in text if c.isdigit())

    return [
        length / 500,              # 長さ
        num_punct / 50,            # 句読点
        num_hira / length,         # ひらがな比率
        num_kata / length,         # カタカナ比率
        num_digit / length,        # 数字比率
    ]


def vectorize(rows):
    """
    rows: [(id, summary, fullOpinion), ...]
    → [vector, vector, ...]
    """
    vectors = []
    for (_id, summary, fullOpinion) in rows:
        v = text_to_vector(summary + fullOpinion)
        vectors.append(v)
    return vectors
