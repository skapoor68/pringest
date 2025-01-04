from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from starlette.middleware.sessions import SessionMiddleware
from datetime import datetime
import secrets
from dotenv import load_dotenv

from pringest import GitHubAPI
from auth import GITHUB_CLIENT_ID, exchange_code_for_token, get_github_user
from server_utils import limiter, EXAMPLE_PRS

load_dotenv()

app = FastAPI()
app.state.limiter = limiter

app.add_middleware(
    SessionMiddleware,
    secret_key=secrets.token_urlsafe(32)
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return _rate_limit_exceeded_handler(request, exc)

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        "index.jinja",
        {
            "request": request,
            "examples": EXAMPLE_PRS,
            "user": request.session.get("user")
        }
    )

@app.get("/login")
async def login(request: Request):
    state = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state
    return RedirectResponse(
        f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&state={state}&scope=repo"
    )

@app.get("/callback")
async def callback(request: Request, code: str, state: str):
    if state != request.session.get("oauth_state"):
       raise HTTPException(status_code=400, detail="Invalid state")
   
    token_data = await exchange_code_for_token(code)
    user_data = await get_github_user(token_data["access_token"])
   
    request.session["user"] = {
       "id": user_data["id"],
       "login": user_data["login"],
       "access_token": token_data["access_token"]
    }
    return RedirectResponse("/")

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/")


@app.post("/", response_class=HTMLResponse)
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
    import re
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
        pass
    except:
        pass
        github_api = GitHubAPI(token=user["access_token"])
        
        pr_info = await github_api.get_pr_info(pr_url)
        diff_text = await github_api.get_pr_diff(pr_info['diff_url'])
        
        created_at = datetime.fromisoformat(pr_info['created_at'].replace('Z', '+00:00'))
        updated_at = datetime.fromisoformat(pr_info['updated_at'].replace('Z', '+00:00'))
        
        pr_summary = (
            f"Title: {pr_info['title']}\n"
            f"Author: {pr_info['author']}\n"
            f"State: {pr_info['state']}\n"
            f"Created: {created_at.strftime('%B %d, %Y')}\n"
        )
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