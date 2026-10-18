import os

import httpx

from src.app.schema.ai import ChatRequest, ChatResponse


class AIServiceError(Exception):
    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


class AIService:
    def __init__(self) -> None:
        self.base_url = os.getenv("AI_SERVICE_URL", "http://127.0.0.1:8090").rstrip("/")

    async def chat(self, request: ChatRequest) -> ChatResponse:
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=310.0) as client:
                response = await client.post(
                    "/chat",
                    json={"messages": [message.model_dump() for message in request.messages]},
                )
                response.raise_for_status()
        except httpx.TimeoutException as error:
            raise AIServiceError("AI service request timed out", 504) from error
        except httpx.HTTPStatusError as error:
            raise AIServiceError("AI service returned an error", 502) from error
        except httpx.RequestError as error:
            raise AIServiceError("AI service is unavailable", 502) from error

        try:
            return ChatResponse.model_validate(response.json())
        except ValueError as error:
            raise AIServiceError("AI service returned an invalid response", 502) from error
