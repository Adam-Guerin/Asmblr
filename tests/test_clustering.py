from app.core.clustering import cluster_texts


def test_cluster_texts():
    texts = ["pain in onboarding", "issue with billing", "onboarding is hard"]
    clusters = cluster_texts(texts, n_clusters=2)
    assert isinstance(clusters, dict)
    assert sum(len(v) for v in clusters.values()) == len(texts)
