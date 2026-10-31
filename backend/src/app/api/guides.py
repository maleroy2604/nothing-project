from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database import database
from src.app.repository.guide import GuideRepository
from src.app.schema.guide import GuideCreate, GuideRead
from src.app.service.guide import GuideNotFoundError, GuideService
from src.logger.logger import logger

router = APIRouter(prefix="/guides", tags=["guides"])


def get_guide_service(
    session: Annotated[AsyncSession, Depends(database.session)],
) -> GuideService:
    return GuideService(GuideRepository(session))


@router.post("/", response_model=GuideRead, status_code=status.HTTP_201_CREATED)
async def create_guide(
    _: GuideCreate,
    service: Annotated[GuideService, Depends(get_guide_service)],
) -> GuideRead:
    guide = await service.create_guide()
    logger.info("Guide created guide_id=%s", guide.id)
    return guide


@router.get("/", response_model=list[GuideRead])
async def list_guides(
    service: Annotated[GuideService, Depends(get_guide_service)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[GuideRead]:
    return await service.list_guides(offset=offset, limit=limit)


@router.get("/{guide_id}", response_model=GuideRead)
async def get_guide(
    guide_id: int,
    service: Annotated[GuideService, Depends(get_guide_service)],
) -> GuideRead:
    try:
        return await service.get_guide(guide_id)
    except GuideNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error
