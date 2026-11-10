from fastapi import APIRouter, HTTPException

from src.app.schema.ai import (
    ChatRequest,
    ChatResponse,
    GuidePlanRequest,
    GuideReviewRequest,
)
from src.app.schema.guide_plan import GuidePlan
from src.app.schema.guide_review import GuideReview
from src.app.service.ai import AIService, AIServiceError
from src.app.service.guide_reviewer import GuideReviewer

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        return await AIService().chat(request)
    except AIServiceError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from error


@router.post("/guide-plan", response_model=GuidePlan)
async def generate_guide_plan(request: GuidePlanRequest) -> GuidePlan:
    try:
        return await AIService().generate_guide_plan(request.topic)
    except AIServiceError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from error


@router.post("/guide-review", response_model=GuideReview)
async def review_guide(request: GuideReviewRequest) -> GuideReview:
    try:
        return await GuideReviewer().review(
            request.guide,
            request.original_request,
        )
    except AIServiceError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from error
