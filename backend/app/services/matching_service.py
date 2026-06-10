import re

from app.services.difficulty_service import DifficultyService
from app.services.llm_service import GeminiService
from app.services.vector_service import VectorService

FRAMEWORK_KEYWORDS = {
    "react", "flutter", "vue", "angular", "svelte", "nextjs", "next.js",
    "typescript", "javascript", "python", "django", "fastapi", "node",
    "java", "kotlin", "swift", "dart", "rust", "go", "tailwind", "css",
}


def extract_skill_keywords(text: str) -> list[str]:
    if not text:
        return []
    lower = text.lower()
    found = [kw for kw in FRAMEWORK_KEYWORDS if kw in lower]
    # also grab explicit comma-separated tokens from bio
    for token in re.split(r"[,;/\s]+", lower):
        token = token.strip()
        if len(token) > 2 and token not in found:
            found.append(token)
    return list(dict.fromkeys(found))[:10]


class MatchingService:
    def __init__(self, vector_service: VectorService, llm_service: GeminiService):
        self.vector = vector_service
        self.llm = llm_service
        self.difficulty = DifficultyService()

    def rank_issues(
        self,
        profile_text: str,
        skill_tags: list[str],
        issues: list[dict],
        explain_top_n: int = 5,
    ) -> list[dict]:
        if not issues:
            return []

        profile_doc = self.vector.build_profile_document(
            bio=profile_text,
            languages=skill_tags,
            skill_tags=skill_tags,
        )
        profile_embedding = self.vector.get_embedding(profile_doc)

        issue_docs = []
        for issue in issues:
            repo_name = issue.get("repo_name", "")
            issue_docs.append(self.vector.build_issue_document(issue, repo_name))

        issue_embeddings = self.vector.batch_embed(issue_docs)
        scored = []

        for idx, issue in enumerate(issues):
            labels = issue.get("labels", [])
            if isinstance(labels, str):
                labels = [l.strip() for l in labels.split(",") if l.strip()]

            cosine = self.vector.calculate_similarity(profile_embedding, issue_embeddings[idx])
            label_boost = self.vector.label_overlap_score(skill_tags, labels) * 0.15
            beginner_boost = 0.05 if any("good" in l.lower() and "issue" in l.lower() for l in labels) else 0.0

            issue_text = f"{issue.get('title', '')} {' '.join(labels)} {issue.get('description', '')}".lower()
            keyword_hits = sum(1 for tag in skill_tags if tag in issue_text)
            keyword_boost = min(0.25, keyword_hits * 0.08)

            final_score = min(1.0, cosine + label_boost + beginner_boost + keyword_boost)
            difficulty, diff_conf = self.difficulty.predict(issue)

            result = {
                **issue,
                "labels": labels,
                "match_score": round(final_score * 100, 2),
                "difficulty": difficulty,
                "difficulty_confidence": round(diff_conf, 2),
                "explanation": None,
            }
            scored.append(result)

        scored.sort(key=lambda x: x["match_score"], reverse=True)

        for i, item in enumerate(scored[:explain_top_n]):
            item["explanation"] = self.llm.explain_match(
                profile_text=profile_text,
                skill_tags=skill_tags,
                issue=item,
                match_score=item["match_score"] / 100,
            )

        return scored
