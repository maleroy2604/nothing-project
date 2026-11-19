from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database import database
from src.app.repository.guide import GuideRepository
from src.app.schema.ai import GuideGenerationRequest
from src.app.schema.guide import GuideCreate, GuideRead, GuideUpdate
from src.app.service.ai import AIService, AIServiceError
from src.app.service.guide import GuideNotFoundError, GuideService
from src.app.service.guide_generation import GuideGenerationService
from src.app.service.guide_generator import (
    GuideGenerationRejectedError,
    GuideGeneratorService,
)
from src.app.service.guide_reviewer import GuideReviewer
from src.logger.logger import logger

router = APIRouter(prefix="/guides", tags=["guides"])


def get_guide_service(
    session: Annotated[AsyncSession, Depends(database.session)],
) -> GuideService:
    return GuideService(GuideRepository(session))


def get_guide_generator_service(
    session: Annotated[AsyncSession, Depends(database.session)],
) -> GuideGeneratorService:
    ai_service = AIService()
    guide_service = GuideService(GuideRepository(session))
    return GuideGeneratorService(
        GuideGenerationService(ai_service),
        GuideReviewer(ai_service),
        guide_service,
    )


@router.post("/", response_model=GuideRead, status_code=status.HTTP_201_CREATED)
async def create_guide(
    _: GuideCreate,
    service: Annotated[GuideService, Depends(get_guide_service)],
) -> GuideRead:
    guide = await service.create_guide()
    logger.info("Guide created guide_id=%s", guide.id)
    return guide


@router.post(
    "/generate",
    response_model=GuideRead,
    status_code=status.HTTP_201_CREATED,
)
async def generate_guide(
    request: GuideGenerationRequest,
    service: Annotated[
        GuideGeneratorService, Depends(get_guide_generator_service)
    ],
) -> GuideRead:
    try:
        guide = await service.generate_guide(request.title)
    except GuideGenerationRejectedError as error:
        logger.info(
            "Generated guide rejected attempts=%s title=%s",
            error.attempts,
            request.title,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": (
                    f"The guide did not pass review after {error.attempts} "
                    f"attempts (final score: "
                    f"{error.final_review.calculated_score}/100)."
                ),
                "guide": error.guide_plan.model_dump(mode="json"),
                "final_review": error.final_review.model_dump(mode="json"),
                "attempts": error.attempts,
            },
        ) from error
    except AIServiceError as error:
        raise HTTPException(
            status_code=error.status_code, detail=str(error)
        ) from error

    logger.info("Generated guide accepted guide_id=%s", guide.id)
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


@router.patch("/{guide_id}", response_model=GuideRead)
async def update_guide(
    guide_id: int,
    data: GuideUpdate,
    service: Annotated[GuideService, Depends(get_guide_service)],
) -> GuideRead:
    try:
        guide = await service.update_guide(
            guide_id,
            title=data.title,
            board_column=data.board_column,
        )
        logger.info("Guide updated guide_id=%s", guide.id)
        return guide
    except GuideNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error


@router.delete("/{guide_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_guide(
    guide_id: int,
    service: Annotated[GuideService, Depends(get_guide_service)],
) -> Response:
    try:
        await service.delete_guide(guide_id)
        logger.info("Guide deleted guide_id=%s", guide_id)
    except GuideNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)
