from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from starlette.middleware.sessions import SessionMiddleware
import secrets

from server_utils import limiter
from routers import auth, index

load_dotenv()

app = FastAPI()
app.state.limiter = limiter

app.add_middleware(
    SessionMiddleware,
    secret_key=secrets.token_urlsafe(32)
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router)
app.include_router(index.router)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return _rate_limit_exceeded_handler(request, exc)