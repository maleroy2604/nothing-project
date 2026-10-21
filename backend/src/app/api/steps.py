from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database import database
from src.app.repository.step import StepRepository
from src.app.schema.step import StepCreate, StepRead, StepUpdate
from src.app.service.step import (
    StepNotFoundError,
    StepQuestNotFoundError,
    StepService,
)

router = APIRouter(prefix="/quests/{quest_id}/steps", tags=["steps"])


def get_step_service(
    session: Annotated[AsyncSession, Depends(database.session)],
) -> StepService:
    return StepService(StepRepository(session))


@router.post("/", response_model=StepRead, status_code=status.HTTP_201_CREATED)
async def create_step(
    quest_id: int,
    data: StepCreate,
    service: Annotated[StepService, Depends(get_step_service)],
) -> StepRead:
    try:
        return await service.create_step(quest_id, data)
    except StepQuestNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error


@router.get("/", response_model=list[StepRead])
async def list_steps(
    quest_id: int,
    service: Annotated[StepService, Depends(get_step_service)],
) -> list[StepRead]:
    try:
        return await service.list_steps(quest_id)
    except StepQuestNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error


@router.patch("/{step_id}", response_model=StepRead)
async def update_step(
    quest_id: int,
    step_id: int,
    data: StepUpdate,
    service: Annotated[StepService, Depends(get_step_service)],
) -> StepRead:
    try:
        return await service.update_step(quest_id, step_id, data)
    except StepNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error
    except StepQuestNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error


@router.delete("/{step_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_step(
    quest_id: int,
    step_id: int,
    service: Annotated[StepService, Depends(get_step_service)],
) -> Response:
    try:
        await service.delete_step(quest_id, step_id)
    except StepNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error
    except StepQuestNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)
