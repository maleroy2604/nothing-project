import os
from contextlib import asynccontextmanager
from typing import Literal

import httpx
from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1)


class ChatResponse(BaseModel):
    model: str
    response: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.ollama_client = httpx.AsyncClient(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/"),
        timeout=httpx.Timeout(300.0, connect=10.0),
    )
    try:
        yield
    finally:
        await app.state.ollama_client.aclose()


app = FastAPI(title="AI Service", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(data: ChatRequest, request: Request) -> ChatResponse:
    client: httpx.AsyncClient = request.app.state.ollama_client
    try:
        response = await client.post(
            "/api/chat",
            json={
                "model": os.getenv("OLLAMA_MODEL", "llama3.2"),
                "messages": [message.model_dump() for message in data.messages],
                "stream": False,
            },
        )
        response.raise_for_status()
    except httpx.TimeoutException as error:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Ollama request timed out",
        ) from error
    except httpx.HTTPStatusError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ollama returned status {error.response.status_code}",
        ) from error
    except httpx.RequestError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Ollama is unavailable",
        ) from error

    try:
        payload = response.json()
        model = payload["model"]
        content = payload["message"]["content"]
    except (KeyError, TypeError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Ollama returned an invalid response",
        ) from error
    if not isinstance(model, str) or not isinstance(content, str):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Ollama returned an invalid response",
        )

    return ChatResponse(model=model, response=content)
