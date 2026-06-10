from typing import Optional

from app.core.config import settings


class GeminiService:
    def __init__(self):
        self._model = None
        self._available = bool(settings.GEMINI_API_KEY)

    def _get_model(self):
        if not self._available:
            return None
        if self._model is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self._model = genai.GenerativeModel(settings.GEMINI_MODEL)
            except Exception:
                self._available = False
                return None
        return self._model

    def explain_match(
        self,
        profile_text: str,
        skill_tags: list[str],
        issue: dict,
        match_score: float,
    ) -> str:
        if not settings.ENABLE_GEMINI_EXPLANATIONS:
            return self._fallback_explanation(skill_tags, issue, match_score)

        model = self._get_model()
        if not model:
            return self._fallback_explanation(skill_tags, issue, match_score)

        labels = issue.get("labels", [])
        if isinstance(labels, str):
            labels = [l.strip() for l in labels.split(",") if l.strip()]

        prompt = f"""You are an open-source contribution advisor. In 1-2 concise sentences, explain why this issue is a good match for this developer. Be specific about overlapping skills. Do not use bullet points.

Developer skills: {', '.join(skill_tags) if skill_tags else profile_text[:300]}
Match score: {match_score:.0%}
Issue: {issue.get('title', '')}
Description: {(issue.get('description') or '')[:400]}
Labels: {', '.join(labels)}"""

        try:
            response = model.generate_content(prompt)
            text = response.text.strip()
            return text if text else self._fallback_explanation(skill_tags, issue, match_score)
        except Exception:
            return self._fallback_explanation(skill_tags, issue, match_score)

    def summarize_codebase(self, repo_name: str, file_tree: list[str]) -> str:
        model = self._get_model()
        if not model or not file_tree:
            return f"Explore the {repo_name} repository structure to find relevant source files."

        files_preview = "\n".join(file_tree[:30])
        prompt = f"""Briefly describe the structure of the {repo_name} repository and suggest 2-3 files a contributor should look at first for open-source issues. Keep it under 3 sentences.

File tree (partial):
{files_preview}"""

        try:
            return model.generate_content(prompt).text.strip()
        except Exception:
            return f"Key directories in {repo_name}: {', '.join(file_tree[:5])}."

    def suggest_learning_resources(self, skill_gaps: list[str]) -> list[dict]:
        model = self._get_model()
        if not model or not skill_gaps:
            return [{"skill": g, "resource_title": f"Learn {g}", "resource_url": f"https://github.com/topics/{g.lower()}"} for g in skill_gaps[:3]]

        prompt = f"""For each missing skill, suggest one free learning resource (official docs or well-known tutorial). Return as simple lines: SKILL | TITLE | URL

Missing skills: {', '.join(skill_gaps)}"""

        try:
            text = model.generate_content(prompt).text.strip()
            resources = []
            for line in text.split("\n"):
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 3:
                    resources.append({
                        "skill": parts[0],
                        "resource_title": parts[1],
                        "resource_url": parts[2],
                    })
            return resources[:5] if resources else self._default_resources(skill_gaps)
        except Exception:
            return self._default_resources(skill_gaps)

    def review_pr(self, issue_title: str, diff_text: str) -> str:
        model = self._get_model()
        if not model:
            return "Gemini API key not configured. Add GEMINI_API_KEY to enable PR review."

        prompt = f"""Review this pull request diff for the issue "{issue_title}". Provide constructive feedback on code quality, potential bugs, and alignment with the issue. Be concise.

Diff:
{diff_text[:4000]}"""

        try:
            return model.generate_content(prompt).text.strip()
        except Exception as e:
            return f"PR review failed: {e}"

    @staticmethod
    def _fallback_explanation(skill_tags: list[str], issue: dict, match_score: float) -> str:
        labels = issue.get("labels", [])
        if isinstance(labels, str):
            labels = [l.strip() for l in labels.split(",") if l.strip()]
        overlap = set(t.lower() for t in skill_tags) & set(l.lower() for l in labels)
        if overlap:
            skills = ", ".join(sorted(overlap))
            return f"Strong overlap with {skills} based on your profile ({match_score:.0%} semantic match)."
        top_skills = ", ".join(skill_tags[:3]) if skill_tags else "your technical background"
        return f"Semantic match ({match_score:.0%}) between your skills in {top_skills} and this issue's requirements."

    @staticmethod
    def _default_resources(skill_gaps: list[str]) -> list[dict]:
        return [
            {
                "skill": g,
                "resource_title": f"{g} documentation",
                "resource_url": f"https://github.com/topics/{g.lower().replace(' ', '-')}",
            }
            for g in skill_gaps[:3]
        ]
