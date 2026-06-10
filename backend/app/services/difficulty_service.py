import re
from typing import Optional


BEGINNER_LABELS = {"good first issue", "good-first-issue", "beginner", "easy", "starter", "first-timers-only"}
HARD_LABELS = {"hard", "complex", "architecture", "refactor", "breaking-change", "epic"}


class DifficultyService:
    def predict(self, issue: dict) -> tuple[str, float]:
        labels = issue.get("labels", [])
        if isinstance(labels, str):
            labels = [l.strip() for l in labels.split(",") if l.strip()]
        labels_lower = {l.lower() for l in labels}

        body = (issue.get("description") or issue.get("body") or "")
        comments = issue.get("comments_count", 0)

        if labels_lower & BEGINNER_LABELS:
            return "easy", 0.85
        if labels_lower & HARD_LABELS:
            return "hard", 0.75

        body_len = len(body)
        if body_len < 200 and comments < 3:
            return "easy", 0.6
        if body_len > 1500 or comments > 15:
            return "hard", 0.65
        if re.search(r"\b(refactor|migrate|redesign|rewrite)\b", body, re.I):
            return "hard", 0.7

        return "medium", 0.55
