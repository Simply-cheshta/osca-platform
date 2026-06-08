import httpx
from fastapi import HTTPException, status

class GitHubClient:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.base_url = "https://api.github.com"

    async def get_user_data(self) -> dict:
        """
        Fetches the primary profile information of the authenticated user.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/user", headers=self.headers)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired GitHub access token."
                )
            return response.json()

    async def get_user_repos(self) -> list:
        """
        Fetches up to 100 repositories owned or contributed to by the user.
        """
        async with httpx.AsyncClient() as client:
            params = {"per_page": 100, "sort": "updated"}
            response = await client.get(f"{self.base_url}/user/repos", headers=self.headers, params=params)
            if response.status_code != 200:
                return []
            return response.json()

    async def fetch_live_issues(self, query_label: str = "good-first-issue") -> list:
        """
        Queries the global GitHub search index for live open issues matching 
        curated accessibility tags (e.g., 'good-first-issue', 'help-wanted').
        """
        async with httpx.AsyncClient() as client:
            query = f"is:issue is:open label:{query_label}"
            params = {
                "q": query,
                "per_page": 20,  
                "sort": "created",
                "order": "desc"
            }
            
            try:
                response = await client.get(
                    f"{self.base_url}/search/issues", 
                    headers=self.headers, 
                    params=params,
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    return []
                
                search_results = response.json()
                items = search_results.get("items", [])
                
                formatted_issues = []
                for index, item in enumerate(items):
                    formatted_issues.append({
                        "id": item.get("id", index),
                        "title": item.get("title", "No Title Provided"),
                        "description": item.get("body", "No description provided.")[:300], 
                        "labels": [label.get("name") for label in item.get("labels", [])],
                        "html_url": item.get("html_url", "")
                    })
                return formatted_issues
                
            except httpx.HTTPError:
                return []