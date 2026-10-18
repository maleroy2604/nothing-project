from fastapi import APIRouter, HTTPException

from src.app.schema.ai import ChatRequest, ChatResponse
from src.app.service.ai import AIService, AIServiceError

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        return await AIService().chat(request)
    except AIServiceError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from error
