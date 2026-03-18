import random


def run_kmeans(vectors, k=3, iterations=3):
    """
    依存ゼロのなんちゃって k-means。
    vectors: [[f1, f2, ...], ...]
    return: [label, label, ...]  (0..k-1)
    """
    if len(vectors) == 0:
        return []

    if len(vectors) < k:
        k = len(vectors)

    centers = random.sample(vectors, k)

    for _ in range(iterations):
        clusters = [[] for _ in range(k)]

        for v in vectors:
            dists = [sum((v[i] - c[i]) ** 2 for i in range(len(v))) for c in centers]
            idx = dists.index(min(dists))
            clusters[idx].append(v)

        new_centers = []
        for group in clusters:
            if not group:
                new_centers.append(random.choice(vectors))
            else:
                dim = len(group[0])
                new_centers.append(
                    [sum(v[i] for v in group) / len(group) for i in range(dim)]
                )
        centers = new_centers

    labels = []
    for v in vectors:
        dists = [sum((v[i] - c[i]) ** 2 for i in range(len(v))) for c in centers]
        labels.append(dists.index(min(dists)))

    return labels
