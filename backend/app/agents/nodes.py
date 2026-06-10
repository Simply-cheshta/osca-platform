from app.agents.state import OSCAState
from app.services.difficulty_service import DifficultyService
from app.services.github_client import GitHubClient, MOCK_ISSUES
from app.services.llm_service import GeminiService
from app.services.matching_service import MatchingService
from app.services.profile_service import ProfileService
from app.services.vector_service import VectorService


def make_nodes(
    vector_service: VectorService,
    llm_service: GeminiService,
    profile_service: ProfileService,
    matching_service: MatchingService,
):
    difficulty_service = DifficultyService()

    async def profile_node(state: OSCAState) -> dict:
        errors = list(state.get("errors", []))
        token = state.get("github_token")
        if not token:
            errors.append("No GitHub token provided")
            return {"errors": errors}

        github = GitHubClient(token)
        user_info = await github.get_user_data()
        repos = await github.get_user_repos()

        languages: dict[str, int] = {}
        for repo in repos:
            lang = repo.get("language")
            if lang:
                languages[lang] = languages.get(lang, 0) + 1

        top_languages = sorted(languages, key=languages.get, reverse=True)[:5]
        skill_tags = [l.lower() for l in top_languages]
        bio = user_info.get("bio") or ""

        profile_text = vector_service.build_profile_document(bio, top_languages, skill_tags)
        skill_profile = {
            "github_username": user_info.get("login"),
            "profile_text": profile_text,
            "skill_tags": skill_tags,
            "top_languages": top_languages,
        }
        return {"profile": user_info, "skill_profile": skill_profile}

    async def discover_issues_node(state: OSCAState) -> dict:
        errors = list(state.get("errors", []))
        token = state.get("github_token")
        github = GitHubClient(token)
        skill_tags = state.get("skill_profile", {}).get("skill_tags", [])
        search_label = skill_tags[0] if skill_tags else None
        issues = await github.search_issues(language=search_label, per_page=30)
        if not issues:
            issues = MOCK_ISSUES
        return {"candidate_issues": issues, "errors": errors}

    async def match_node(state: OSCAState) -> dict:
        skill_profile = state.get("skill_profile", {})
        issues = state.get("candidate_issues", [])
        if not skill_profile or not issues:
            return {"ranked_matches": []}

        ranked = matching_service.rank_issues(
            profile_text=skill_profile.get("profile_text", ""),
            skill_tags=skill_profile.get("skill_tags", []),
            issues=issues,
            explain_top_n=5,
        )
        return {"ranked_matches": ranked}

    async def learning_gap_node(state: OSCAState) -> dict:
        skill_profile = state.get("skill_profile", {})
        ranked = state.get("ranked_matches", [])
        user_tags = set(skill_profile.get("skill_tags", []))

        gaps: list[str] = []
        for match in ranked[:3]:
            labels = match.get("labels", [])
            for label in labels:
                if label.lower() not in user_tags and label.lower() not in {"good first issue", "help wanted", "bug"}:
                    gaps.append(label)

        unique_gaps = list(dict.fromkeys(gaps))[:5]
        resources = llm_service.suggest_learning_resources(unique_gaps) if unique_gaps else []
        return {"learning_gaps": unique_gaps, "learning_resources": resources}

    async def codebase_node(state: OSCAState) -> dict:
        ranked = state.get("ranked_matches", [])
        token = state.get("github_token")
        insights: dict = {}

        if not ranked or not token:
            return {"codebase_insights": insights}

        top = ranked[0]
        repo_name = top.get("repo_name", "")
        if "/" not in repo_name:
            return {"codebase_insights": insights}

        owner, repo = repo_name.split("/", 1)
        github = GitHubClient(token)
        files = await github.get_repo_contents(owner, repo)
        summary = llm_service.summarize_codebase(repo_name, files)
        insights[repo_name] = {"files": files[:20], "summary": summary}
        return {"codebase_insights": insights}

    return {
        "profile": profile_node,
        "discover_issues": discover_issues_node,
        "match": match_node,
        "learning_gaps": learning_gap_node,
        "codebase": codebase_node,
    }
