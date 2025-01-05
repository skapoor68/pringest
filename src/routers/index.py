from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
import re

from pringest import GitHubAPI
from server_utils import limiter, EXAMPLE_PRS

router = APIRouter(tags=["pull_requests"])
templates = Jinja2Templates(directory="templates")

@router.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        "index.jinja",
        {
            "request": request,
            "examples": EXAMPLE_PRS,
            "user": request.session.get("user")
        }
    )

@router.post("/", response_class=HTMLResponse)
@limiter.limit("10/minute")
async def process_pr(
    request: Request,
    pr_url: str = Form(...),
):
    """Process a GitHub PR URL and return the analyzed results."""
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login")
    
    # URL validation
    if not re.match(r'^(?:https?://)?github\.com/[^/]+/[^/]+/pull/\d+', pr_url):
        return templates.TemplateResponse(
            "index.jinja",
            {
                "request": request,
                "user": user,
                "error_message": "Invalid GitHub PR URL format. Expected form: github.com/<owner>/<repo>/pull/<number>",
                "pr_url": pr_url,
                "examples": EXAMPLE_PRS
            }
        )
    
    try:
        github_api = GitHubAPI(token=user["access_token"])
        pr_info = await github_api.get_pr_info(pr_url)
        diff_text = await github_api.get_pr_diff(pr_info['diff_url'])
        patch_text = await github_api.get_pr_patch(pr_info['patch_url'])
        
        created_at = datetime.fromisoformat(pr_info['created_at'].replace('Z', '+00:00'))
        updated_at = datetime.fromisoformat(pr_info['updated_at'].replace('Z', '+00:00'))
        
        pr_summary = (
            f"Title: {pr_info['title']}\n"
            f"Author: {pr_info['author']}\n"
            f"State: {pr_info['state']}\n"
            f"Created: {created_at.strftime('%B %d, %Y')}\n"
            f"Last Updated: {updated_at.strftime('%B %d, %Y')}\n"
            f"Files Changed: {pr_info['files_changed']}\n"
            f"Lines Added: {pr_info['additions']}\n"
            f"Lines Deleted: {pr_info['deletions']}\n\n"
            f"Description:\n{pr_info['body']}"
        )
        
        return templates.TemplateResponse(
            "index.jinja",
            {
                "request": request,
                "user": user,
                "result": True,
                "pr_url": pr_url,
                "pr_summary": pr_summary,
                "files_changed": pr_info['files_summary'],
                "pr_diff": diff_text,
                "pr_patch": patch_text,
                "examples": EXAMPLE_PRS
            }
        )
    except HTTPException as e:
        error_message = str(e.detail)
        if e.status_code == 404:
            error_message = "Pull request not found or repository is private"
        elif e.status_code == 403:
            error_message = "API rate limit exceeded. Please try again later"
            
        return templates.TemplateResponse(
            "index.jinja",
            {
                "request": request,
                "user": user,
                "error_message": error_message,
                "pr_url": pr_url,
                "examples": EXAMPLE_PRS
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "index.jinja",
            {
                "request": request,
                "user": user,
                "error_message": f"Error: {str(e)}",
                "pr_url": pr_url,
                "examples": EXAMPLE_PRS
            }
        )