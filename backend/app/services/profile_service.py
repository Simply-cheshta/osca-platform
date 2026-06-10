from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.user import SkillProfile, User
from app.services.github_client import GitHubClient
from app.services.vector_service import VectorService

FRONTEND_LANGUAGES = {"JavaScript", "TypeScript", "HTML", "CSS", "Vue", "Svelte", "React"}
BACKEND_LANGUAGES = {"Python", "Java", "Go", "Rust", "Ruby", "C#", "C++", "PHP", "Kotlin", "Swift"}


class ProfileService:
    def __init__(self, vector_service: VectorService):
        self.vector = vector_service

    async def analyze_and_persist(self, user: User, db: Session) -> dict:
        from app.core.security import decrypt_token

        token = decrypt_token(user.access_token_encrypted) if user.access_token_encrypted else None
        if not token:
            raise ValueError("No GitHub token stored for user")

        github = GitHubClient(token)
        user_info = await github.get_user_data()
        repos = await github.get_user_repos()

        languages_count: dict[str, int] = {}
        total_stars = 0
        repo_names: list[str] = []

        for repo in repos:
            total_stars += repo.get("stargazers_count", 0)
            lang = repo.get("language")
            if lang:
                languages_count[lang] = languages_count.get(lang, 0) + 1
            repo_names.append(repo.get("full_name", repo.get("name", "")))

        top_languages = sorted(languages_count, key=languages_count.get, reverse=True)[:5]
        skill_tags = [l.lower() for l in top_languages]

        fe = sum(c for lang, c in languages_count.items() if lang in FRONTEND_LANGUAGES)
        be = sum(c for lang, c in languages_count.items() if lang in BACKEND_LANGUAGES)
        total = sum(languages_count.values()) or 1

        frontend_score = round(min((fe / total) * 10, 10.0), 1)
        backend_score = round(min((be / total) * 10, 10.0), 1)
        dsa_score = round(
            min((languages_count.get("C++", 0) + languages_count.get("Java", 0) + languages_count.get("Python", 0)) / total * 7 + 3.0, 10.0),
            1,
        )

        bio = user_info.get("bio") or user.bio or ""
        has_bio = 1 if bio else 0
        os_readiness = min(len(repos) * 5 + min(total_stars * 2, 20) + has_bio * 20 + 20, 100)

        if frontend_score > backend_score + 2:
            experience_level = "frontend-focused"
        elif backend_score > frontend_score + 2:
            experience_level = "backend-focused"
        elif len(repos) < 5:
            experience_level = "beginner"
        else:
            experience_level = "intermediate"

        profile_text = self.vector.build_profile_document(
            bio=bio,
            languages=top_languages,
            skill_tags=skill_tags,
            repo_names=repo_names,
        )

        user.bio = bio
        user.avatar_url = user_info.get("avatar_url")
        user.email = user_info.get("email")

        profile = db.query(SkillProfile).filter(SkillProfile.user_id == user.id).first()
        if not profile:
            profile = SkillProfile(user_id=user.id)
            db.add(profile)

        profile.profile_text = profile_text
        profile.top_languages = ",".join(top_languages)
        profile.skill_tags = ",".join(skill_tags)
        profile.experience_level = experience_level
        profile.frontend_score = int(frontend_score)
        profile.backend_score = int(backend_score)
        profile.dsa_score = int(dsa_score)
        profile.open_source_readiness = int(os_readiness)
        profile.last_synced_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(profile)

        return {
            "github_username": user.github_username,
            "avatar_url": user.avatar_url,
            "public_repos": user_info.get("public_repos"),
            "bio": bio,
            "top_languages": top_languages,
            "skill_tags": skill_tags,
            "profile_text": profile_text,
            "experience_level": experience_level,
            "metrics": {
                "frontend_score": frontend_score,
                "backend_score": backend_score,
                "dsa_score": dsa_score,
                "open_source_readiness": f"{os_readiness}%",
            },
        }

    @staticmethod
    def get_profile_dict(user: User, db: Session) -> dict | None:
        profile = db.query(SkillProfile).filter(SkillProfile.user_id == user.id).first()
        if not profile:
            return None
        top_langs = [l for l in (profile.top_languages or "").split(",") if l]
        tags = [t for t in (profile.skill_tags or "").split(",") if t]
        return {
            "github_username": user.github_username,
            "avatar_url": user.avatar_url,
            "bio": user.bio,
            "top_languages": top_langs,
            "skill_tags": tags,
            "profile_text": profile.profile_text,
            "experience_level": profile.experience_level,
            "metrics": {
                "frontend_score": profile.frontend_score,
                "backend_score": profile.backend_score,
                "dsa_score": profile.dsa_score,
                "open_source_readiness": f"{profile.open_source_readiness}%",
            },
        }
