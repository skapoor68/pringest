from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
import secrets

from auth_utils import GITHUB_CLIENT_ID, exchange_code_for_token, get_github_user

router = APIRouter(tags=["auth"])

@router.get("/login")
async def login(request: Request):
    state = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state
    return RedirectResponse(
        f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&state={state}&scope=repo"
    )

@router.get("/callback")
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

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/")