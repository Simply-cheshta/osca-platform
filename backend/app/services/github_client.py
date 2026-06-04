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