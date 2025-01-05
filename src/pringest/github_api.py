import os
import re
from typing import Optional, Tuple
import aiohttp
from fastapi import HTTPException

class GitHubAPI:
    """Handles GitHub API interactions for PR information retrieval."""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"
        
    @staticmethod
    def parse_pr_url(url: str) -> Tuple[str, str, int]:
        """Extract owner, repo, and PR number from GitHub PR URL."""
        pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
        match = re.search(pattern, url)
        if not match:
            raise ValueError("Invalid GitHub PR URL. Expected format: https://github.com/owner/repo/pull/number")
        return match.group(1), match.group(2), int(match.group(3))

    async def _make_request(self, endpoint: str) -> dict:
        """Make an authenticated request to the GitHub API."""
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(f"{self.base_url}{endpoint}") as resp:
                if resp.status == 404:
                    raise HTTPException(status_code=404, detail="PR not found or repository is private")
                elif resp.status == 403:
                    raise HTTPException(status_code=403, detail="API rate limit exceeded")
                elif resp.status != 200:
                    raise HTTPException(status_code=resp.status, detail="GitHub API request failed")
                return await resp.json()
            
    async def get_pr_diff(self, diff_url: str) -> str:
        """Fetch the PR diff text from the diff URL."""
        async with aiohttp.ClientSession() as session:
            async with session.get(diff_url) as resp:
                if resp.status != 200:
                    raise HTTPException(status_code=resp.status, detail="Failed to fetch PR diff")
                return await resp.text()
            
    async def get_pr_patch(self, patch_url: str) -> str:
        """Fetch the PR patch text from the patch URL."""
        async with aiohttp.ClientSession() as session:
            async with session.get(patch_url) as resp:
                if resp.status != 200:
                    raise HTTPException(status_code=resp.status, detail="Failed to fetch PR patch")
                return await resp.text()
        
    async def get_pr_info(self, pr_url: str) -> dict:
        """Fetch PR information including title, description, and file changes."""
        try:
            owner, repo, pr_number = self.parse_pr_url(pr_url)
            
            # Fetch PR details
            pr_endpoint = f"/repos/{owner}/{repo}/pulls/{pr_number}"
            pr_data = await self._make_request(pr_endpoint)
            
            # Fetch PR files
            files_endpoint = f"{pr_endpoint}/files"
            files_data = await self._make_request(files_endpoint)

            # Get PR diff if available
            diff = pr_data.get("diff_url", "Diff not available")
            patch = pr_data.get("patch_url", "Patch not available")

            # Generate files summary with additions/deletions
            files_summary = "\n".join(
                f"{f['filename']} ({f['status']}, +{f['additions']}/-{f['deletions']})" 
                for f in files_data
            )
            
            return {
                "title": pr_data["title"],
                "body": pr_data.get("body", "No description provided"),
                "state": pr_data["state"],
                "files_changed": len(files_data),
                "additions": sum(f["additions"] for f in files_data),
                "deletions": sum(f["deletions"] for f in files_data),
                "files_summary": files_summary,
                "diff_url": diff,
                "patch_url": patch,
                "author": pr_data["user"]["login"],
                "created_at": pr_data["created_at"],
                "updated_at": pr_data["updated_at"]
            }
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except aiohttp.ClientError as e:
            raise HTTPException(status_code=500, detail=f"Failed to connect to GitHub API: {str(e)}")