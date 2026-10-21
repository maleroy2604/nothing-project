from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.app.api.ai import router as ai_router
from src.app.api.guides import router as guides_router
from src.app.api.quests import router as quests_router
from src.app.api.steps import router as steps_router
from src.app.database import database


@asynccontextmanager
async def lifespan(_: FastAPI):
    await database.start()
    yield
    await database.stop()


app = FastAPI(lifespan=lifespan)
app.include_router(ai_router)
app.include_router(guides_router)
app.include_router(quests_router)
app.include_router(steps_router)
