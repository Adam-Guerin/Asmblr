from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans


def cluster_texts(texts: List[str], n_clusters: int = 5) -> Dict[int, List[str]]:
    if not texts:
        return {}
    n_clusters = min(n_clusters, max(1, len(texts)))
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf = vectorizer.fit_transform(texts)
    if tfidf.shape[0] < n_clusters:
        n_clusters = tfidf.shape[0]
    model = KMeans(n_clusters=n_clusters, n_init=5, random_state=42)
    labels = model.fit_predict(tfidf)
    clusters: Dict[int, List[str]] = {}
    for text, label in zip(texts, labels):
        clusters.setdefault(int(label), []).append(text)
    return clusters
