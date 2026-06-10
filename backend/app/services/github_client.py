import httpx
from fastapi import HTTPException, status


class GitHubClient:
    def __init__(self, access_token: str | None = None):
        self.access_token = access_token
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        if access_token:
            self.headers["Authorization"] = f"Bearer {access_token}"
        self.base_url = "https://api.github.com"

    async def get_user_data(self) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/user", headers=self.headers)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired GitHub access token.",
                )
            return response.json()

    async def get_user_repos(self) -> list:
        async with httpx.AsyncClient() as client:
            params = {"per_page": 100, "sort": "updated"}
            response = await client.get(
                f"{self.base_url}/user/repos", headers=self.headers, params=params
            )
            return response.json() if response.status_code == 200 else []

    async def fetch_live_issues(
        self,
        query_label: str = "good-first-issue",
        language: str | None = None,
        per_page: int = 20,
    ) -> list:
        async with httpx.AsyncClient() as client:
            query = f'is:issue is:open label:"{query_label}"'
            if language:
                query += f" label:{language}"
            params = {"q": query, "per_page": per_page, "sort": "updated", "order": "desc"}

            try:
                response = await client.get(
                    f"{self.base_url}/search/issues",
                    headers=self.headers,
                    params=params,
                    timeout=15.0,
                )
                if response.status_code != 200:
                    return []
                return self._format_issues(response.json().get("items", []))
            except httpx.HTTPError:
                return []

    async def search_issues(
        self,
        language: str | None = None,
        per_page: int = 30,
    ) -> list:
        label = "good first issue"
        issues = await self.fetch_live_issues(query_label=label, language=language, per_page=per_page)
        if issues:
            return issues
        # Broader fallback if label+language combo returns nothing
        if language:
            return await self.fetch_live_issues(query_label=label, language=None, per_page=per_page)
        return []

    async def get_repo_contents(self, owner: str, repo: str, path: str = "") -> list:
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
            response = await client.get(url, headers=self.headers, timeout=10.0)
            if response.status_code != 200:
                return []
            data = response.json()
            if isinstance(data, list):
                return [item.get("path", "") for item in data]
            return [data.get("path", "")]

    async def get_user_pull_requests(self) -> list:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/search/issues",
                headers=self.headers,
                params={"q": "is:pr author:@me", "per_page": 20, "sort": "updated"},
                timeout=10.0,
            )
            if response.status_code != 200:
                return []
            return [
                {
                    "title": item.get("title"),
                    "html_url": item.get("html_url"),
                    "state": item.get("state"),
                    "repo": item.get("repository_url", "").split("/repos/")[-1],
                }
                for item in response.json().get("items", [])
            ]

    @staticmethod
    def _format_issues(items: list) -> list:
        formatted = []
        for item in items:
            repo_url = item.get("repository_url", "")
            repo_name = repo_url.split("/repos/")[-1] if repo_url else ""
            labels = [label.get("name", "") for label in item.get("labels", [])]
            formatted.append({
                "id": item.get("id"),
                "title": item.get("title", "No Title"),
                "description": (item.get("body") or "No description provided.")[:500],
                "labels": labels,
                "html_url": item.get("html_url", ""),
                "repo_name": repo_name,
                "comments_count": item.get("comments", 0),
            })
        return formatted


MOCK_ISSUES = [
    {
        "id": 1001,
        "title": "Build dynamic UI panels with React hooks",
        "description": "Refactor interface components using modern React hooks and TypeScript.",
        "labels": ["good first issue", "frontend", "react"],
        "html_url": "https://github.com/facebook/react/issues/1",
        "repo_name": "facebook/react",
        "comments_count": 2,
    },
    {
        "id": 1002,
        "title": "Fix responsive layout in Tailwind CSS components",
        "description": "CSS elements are overlapping across responsive breakpoints in the dashboard.",
        "labels": ["good first issue", "frontend", "css"],
        "html_url": "https://github.com/tailwindlabs/tailwindcss/issues/1",
        "repo_name": "tailwindlabs/tailwindcss",
        "comments_count": 1,
    },
    {
        "id": 1003,
        "title": "Add FastAPI endpoint for user preferences",
        "description": "Implement a new REST endpoint using Python FastAPI for user settings.",
        "labels": ["good first issue", "backend", "python"],
        "html_url": "https://github.com/tiangolo/fastapi/issues/1",
        "repo_name": "tiangolo/fastapi",
        "comments_count": 0,
    },
]
