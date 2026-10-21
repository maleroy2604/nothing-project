from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database import database
from src.app.repository.quest import QuestRepository
from src.app.schema.quest import QuestCreate, QuestRead, QuestUpdate
from src.app.service.quest import (
    QuestGuideNotFoundError,
    QuestNotFoundError,
    QuestService,
)

router = APIRouter(prefix="/quests", tags=["quests"])


def get_quest_service(
    session: Annotated[AsyncSession, Depends(database.session)],
) -> QuestService:
    return QuestService(QuestRepository(session))


@router.post("/", response_model=QuestRead, status_code=status.HTTP_201_CREATED)
async def create_quest(
    data: QuestCreate,
    service: Annotated[QuestService, Depends(get_quest_service)],
) -> QuestRead:
    try:
        return await service.create_quest(data)
    except QuestGuideNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error


@router.get("/", response_model=list[QuestRead])
async def list_quests(
    service: Annotated[QuestService, Depends(get_quest_service)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    guide_id: Annotated[int | None, Query(gt=0)] = None,
) -> list[QuestRead]:
    return await service.list_quests(
        offset=offset, limit=limit, guide_id=guide_id
    )


@router.get("/{quest_id}", response_model=QuestRead)
async def get_quest(
    quest_id: int,
    service: Annotated[QuestService, Depends(get_quest_service)],
) -> QuestRead:
    try:
        return await service.get_quest(quest_id)
    except QuestNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.patch("/{quest_id}", response_model=QuestRead)
async def update_quest(
    quest_id: int,
    data: QuestUpdate,
    service: Annotated[QuestService, Depends(get_quest_service)],
) -> QuestRead:
    try:
        return await service.update_quest(quest_id, data)
    except QuestNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except QuestGuideNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error


@router.delete("/{quest_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quest(
    quest_id: int,
    service: Annotated[QuestService, Depends(get_quest_service)],
) -> Response:
    try:
        await service.delete_quest(quest_id)
    except QuestNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)
