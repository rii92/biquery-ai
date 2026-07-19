import base64
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.webhook import router as webhook_router
from app.api.query import router as query_router
from app.api.config import router as config_router
from app.api.intents import router as intents_router
from app.api.analyze import router as analyze_router
from app.core.config import DASHBOARD_USERNAME, DASHBOARD_PASSWORD

app = FastAPI(title="BP Batam Ai — BP Batam", version="2.0.0")

static_dir = Path(__file__).resolve().parent.parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if DASHBOARD_PASSWORD:
        path = request.url.path
        if not path.startswith("/webhook"):
            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Basic "):
                return Response(
                    status_code=401,
                    headers={"WWW-Authenticate": 'Basic realm="BP Batam Ai"'},
                    content='{"detail":"Unauthorized"}',
                    media_type="application/json",
                )
            try:
                decoded = base64.b64decode(auth.removeprefix("Basic ")).decode()
                username, password = decoded.split(":", 1)
            except Exception:
                return Response(
                    status_code=401,
                    headers={"WWW-Authenticate": 'Basic realm="BP Batam Ai"'},
                )
            if username != DASHBOARD_USERNAME or password != DASHBOARD_PASSWORD:
                return Response(
                    status_code=401,
                    headers={"WWW-Authenticate": 'Basic realm="BP Batam Ai"'},
                )
    return await call_next(request)


@app.get("/")
def index():
    return FileResponse(str(static_dir / "index.html"))


app.include_router(webhook_router)
app.include_router(query_router)
app.include_router(config_router)
app.include_router(intents_router)
app.include_router(analyze_router)


@app.get("/intents")
def intents_page():
    return FileResponse(str(static_dir / "intents.html"))
