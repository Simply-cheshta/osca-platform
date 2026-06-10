import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import settings


class VectorService:
    def __init__(self):
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)

    def get_embedding(self, text: str) -> np.ndarray:
        return self.model.encode(text or "", convert_to_numpy=True)

    def batch_embed(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.array([])
        return self.model.encode(texts, convert_to_numpy=True)

    def calculate_similarity(self, bio_embedding: np.ndarray, issue_embedding: np.ndarray) -> float:
        dot_product = np.dot(bio_embedding, issue_embedding)
        norm_bio = np.linalg.norm(bio_embedding)
        norm_issue = np.linalg.norm(issue_embedding)
        if norm_bio == 0 or norm_issue == 0:
            return 0.0
        return float(dot_product / (norm_bio * norm_issue))

    @staticmethod
    def build_profile_document(
        bio: str,
        languages: list[str],
        skill_tags: list[str],
        repo_names: list[str] | None = None,
    ) -> str:
        parts = [
            f"Developer profile: {bio or 'Open source contributor'}.",
            f"Primary languages: {', '.join(languages) if languages else 'general programming'}.",
            f"Skills: {', '.join(skill_tags) if skill_tags else 'software development'}.",
        ]
        if repo_names:
            parts.append(f"Recent repositories: {', '.join(repo_names[:5])}.")
        return " ".join(parts)

    @staticmethod
    def build_issue_document(issue: dict, repo_name: str = "") -> str:
        labels = issue.get("labels", [])
        if isinstance(labels, str):
            labels = [l.strip() for l in labels.split(",") if l.strip()]
        title = issue.get("title", "")
        body = (issue.get("description") or issue.get("body") or "")[:2000]
        label_str = ", ".join(labels) if labels else ""
        repo_part = f"Repository: {repo_name}. " if repo_name else ""
        return f"Issue: {title}. {body} Labels: {label_str}. {repo_part}"

    @staticmethod
    def label_overlap_score(profile_tags: list[str], issue_labels: list[str]) -> float:
        if not profile_tags or not issue_labels:
            return 0.0
        p = {t.lower() for t in profile_tags}
        i = {l.lower() for l in issue_labels}
        intersection = p & i
        union = p | i
        return len(intersection) / len(union) if union else 0.0
