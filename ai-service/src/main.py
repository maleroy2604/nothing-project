import json
import logging
import os
from contextlib import asynccontextmanager
from typing import Any, Literal

import httpx
from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel, Field

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_MODEL = "openai/gpt-oss-20b"
DEFAULT_TIMEOUT_SECONDS = 180.0
SUPPORTED_OPTIONS = {
    "frequency_penalty",
    "max_completion_tokens",
    "max_tokens",
    "presence_penalty",
    "seed",
    "stop",
    "temperature",
    "top_p",
}
logger = logging.getLogger("uvicorn.error")


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1)
    format: str | dict[str, Any] | None = None
    options: dict[str, Any] | None = None


class ChatResponse(BaseModel):
    model: str
    response: str


def build_groq_payload(data: ChatRequest, model: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": model,
        "messages": [message.model_dump() for message in data.messages],
    }
    if isinstance(data.format, dict):
        payload["messages"].insert(
            0,
            {
                "role": "system",
                "content": (
                    "Return only a valid JSON object that conforms to this "
                    "JSON Schema. Do not include markdown or any text outside "
                    "the JSON object:\n"
                    f"{json.dumps(data.format, ensure_ascii=False)}"
                ),
            },
        )
        payload["response_format"] = {"type": "json_object"}
    elif data.format is not None:
        if data.format.lower() not in ("json", "json_object"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Groq supports only JSON response formats",
            )
        payload["response_format"] = {"type": "json_object"}
    if data.options is not None:
        unsupported_options = data.options.keys() - SUPPORTED_OPTIONS
        if unsupported_options:
            names = ", ".join(sorted(unsupported_options))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported Groq options: {names}",
            )
        payload.update(data.options)
    return payload


def get_groq_error_message(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return "Groq returned an error"

    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict) and isinstance(error.get("message"), str):
            return error["message"]
        if isinstance(payload.get("detail"), str):
            return payload["detail"]
    return "Groq returned an error"


@asynccontextmanager
async def lifespan(app: FastAPI):
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    app.state.groq_api_key = api_key
    app.state.groq_model = os.getenv("GROQ_MODEL", DEFAULT_MODEL)
    timeout = float(
        os.getenv("GROQ_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS))
    )
    app.state.groq_client = httpx.AsyncClient(
        base_url=GROQ_BASE_URL,
        timeout=httpx.Timeout(timeout, connect=10.0),
        headers={"Authorization": f"Bearer {api_key}"} if api_key else {},
    )
    try:
        yield
    finally:
        await app.state.groq_client.aclose()


app = FastAPI(title="AI Service", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(data: ChatRequest, request: Request) -> ChatResponse:
    if not request.app.state.groq_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GROQ_API_KEY is not configured",
        )

    client: httpx.AsyncClient = request.app.state.groq_client
    model = request.app.state.groq_model
    payload = build_groq_payload(data, model)
    try:
        response = await client.post("/chat/completions", json=payload)
        response.raise_for_status()
    except httpx.TimeoutException as error:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Groq request timed out",
        ) from error
    except httpx.HTTPStatusError as error:
        upstream_status = error.response.status_code
        logger.error(
            "Groq request failed status=%s response_body=%s",
            upstream_status,
            error.response.text,
        )
        mapped_status = (
            status.HTTP_429_TOO_MANY_REQUESTS
            if upstream_status == status.HTTP_429_TOO_MANY_REQUESTS
            else status.HTTP_502_BAD_GATEWAY
        )
        raise HTTPException(
            status_code=mapped_status,
            detail=(
                f"Groq returned status {upstream_status}: "
                f"{get_groq_error_message(error.response)}"
            ),
        ) from error
    except httpx.RequestError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Groq is unavailable",
        ) from error

    try:
        result = response.json()
        returned_model = result["model"]
        content = result["choices"][0]["message"]["content"]
    except (IndexError, KeyError, TypeError, ValueError) as error:
        logger.exception("Groq returned an unexpected completion response")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Groq returned an invalid response",
        ) from error
    if not isinstance(returned_model, str) or not isinstance(content, str):
        logger.error("Groq returned invalid completion fields: %r", result)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Groq returned an invalid response",
        )

    logger.info("Groq completion model=%s response=%s", returned_model, content)
    return ChatResponse(model=returned_model, response=content)
