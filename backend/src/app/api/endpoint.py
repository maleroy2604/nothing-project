from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, Request

from src.app.api.ai import router as ai_router
from src.app.api.guides import router as guides_router
from src.app.api.quests import router as quests_router
from src.app.api.steps import router as steps_router
from src.app.database import database
from src.logger.logger import logger


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Starting API and checking database migrations")
    try:
        await database.start()
        logger.info("API startup completed")
        yield
    finally:
        logger.info("Shutting down API")
        await database.stop()
        logger.info("API shutdown completed")


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (perf_counter() - start_time) * 1000
        logger.exception(
            "Request failed method=%s path=%s duration_ms=%.2f",
            request.method,
            request.url.path,
            duration_ms,
        )
        raise

    duration_ms = (perf_counter() - start_time) * 1000
    logger.info(
        "Request completed method=%s path=%s status_code=%s duration_ms=%.2f",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


app.include_router(ai_router)
app.include_router(guides_router)
app.include_router(quests_router)
app.include_router(steps_router)
