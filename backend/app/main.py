import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.auth.router import router as auth_router
from app.core.arq import create_arq_pool
from app.core.database import AsyncSessionLocal
from app.core.logging import setup_logging
from app.core.redis import create_redis_pool
from app.exceptions import OAuthError, UserNotFoundError
from app.users.router import router as users_router

setup_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = create_redis_pool()
    app.state.arq = await create_arq_pool()
    yield
    await app.state.redis.aclose()
    await app.state.arq.aclose()


app = FastAPI(title="Coders API", version="0.1.0", lifespan=lifespan)


@app.exception_handler(UserNotFoundError)
async def user_not_found_handler(
    request: Request, exc: UserNotFoundError
) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": "User not found"})


@app.exception_handler(OAuthError)
async def oauth_error_handler(request: Request, exc: OAuthError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


app.include_router(auth_router)
app.include_router(users_router)


@app.get("/health")
async def health(request: Request) -> JSONResponse:
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Database health check failed")
        return JSONResponse(
            status_code=503,
            content={"status": "error", "detail": "database unavailable"},
        )
    try:
        await request.app.state.redis.ping()
    except Exception:
        logger.exception("Redis health check failed")
        return JSONResponse(
            status_code=503, content={"status": "error", "detail": "redis unavailable"}
        )
    return JSONResponse(content={"status": "ok"})
