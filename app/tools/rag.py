from pathlib import Path
from typing import List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class RAGPlaybookQA:
    def __init__(self, knowledge_dir: Path) -> None:
        self.knowledge_dir = knowledge_dir
        self.docs = self._load_docs()
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = self.vectorizer.fit_transform(self.docs) if self.docs else None

    def _load_docs(self) -> List[str]:
        docs = []
        for path in self.knowledge_dir.glob("*.md"):
            docs.append(path.read_text(encoding="utf-8"))
        return docs

    def query(self, question: str, k: int = 2) -> str:
        if not self.docs or self.matrix is None:
            return ""
        query_vec = self.vectorizer.transform([question])
        scores = cosine_similarity(query_vec, self.matrix).flatten()
        top_indices = scores.argsort()[-k:][::-1]
        return "\n---\n".join([self.docs[i] for i in top_indices])
