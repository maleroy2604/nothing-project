import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
from fastapi import HTTPException

from src.main import GROQ_BASE_URL, ChatRequest, app, build_groq_payload, chat, lifespan


def make_request(
    *,
    api_key: str = "test-key",
    model: str = "openai/gpt-oss-20b",
    client: AsyncMock | None = None,
) -> SimpleNamespace:
    state = SimpleNamespace(
        groq_api_key=api_key,
        groq_model=model,
        groq_client=client or AsyncMock(),
    )
    return SimpleNamespace(app=SimpleNamespace(state=state))


class GroqPayloadTests(unittest.TestCase):
    def test_schema_format_uses_json_mode_and_includes_schema_in_prompt(self) -> None:
        schema = {
            "type": "object",
            "properties": {"answer": {"type": "string"}},
        }
        request = ChatRequest(
            messages=[{"role": "user", "content": "Answer"}],
            format=schema,
            options={"temperature": 0.0, "seed": 42},
        )

        payload = build_groq_payload(request, "openai/gpt-oss-20b")

        self.assertEqual(payload["response_format"], {"type": "json_object"})
        self.assertIn("Return only a valid JSON object", payload["messages"][0]["content"])
        self.assertIn('"properties": {"answer": {"type": "string"}}', payload["messages"][0]["content"])
        self.assertEqual(payload["messages"][1]["content"], "Answer")
        self.assertEqual(payload["temperature"], 0.0)
        self.assertEqual(payload["seed"], 42)

    def test_json_format_is_translated_to_json_object_mode(self) -> None:
        request = ChatRequest(
            messages=[{"role": "user", "content": "Answer"}],
            format="json",
        )

        payload = build_groq_payload(request, "openai/gpt-oss-20b")

        self.assertEqual(payload["response_format"], {"type": "json_object"})

    def test_unsupported_format_is_rejected(self) -> None:
        request = ChatRequest(
            messages=[{"role": "user", "content": "Answer"}],
            format="xml",
        )

        with self.assertRaises(HTTPException) as raised:
            build_groq_payload(request, "openai/gpt-oss-20b")

        self.assertEqual(raised.exception.status_code, 400)

    def test_unsupported_option_is_rejected(self) -> None:
        request = ChatRequest(
            messages=[{"role": "user", "content": "Answer"}],
            options={"model": "another-model"},
        )

        with self.assertRaises(HTTPException) as raised:
            build_groq_payload(request, "openai/gpt-oss-20b")

        self.assertEqual(raised.exception.status_code, 400)


class GroqChatTests(unittest.IsolatedAsyncioTestCase):
    async def test_lifespan_uses_configured_api_key_as_bearer_token(self) -> None:
        client = AsyncMock()
        with patch.dict("os.environ", {"GROQ_API_KEY": "test-key"}):
            with patch(
                "src.main.httpx.AsyncClient",
                return_value=client,
            ) as create_client:
                async with lifespan(app):
                    self.assertEqual(
                        create_client.call_args.kwargs["headers"],
                        {"Authorization": "Bearer test-key"},
                    )

        client.aclose.assert_awaited_once()

    async def test_completion_url_uses_groq_api_path_once(self) -> None:
        async with httpx.AsyncClient(base_url=GROQ_BASE_URL) as client:
            url = client.build_request("POST", "/chat/completions").url

        self.assertEqual(
            str(url),
            "https://api.groq.com/openai/v1/chat/completions",
        )

    async def test_missing_api_key_returns_configuration_error(self) -> None:
        client = AsyncMock()
        request = make_request(api_key="", client=client)
        data = ChatRequest(
            messages=[{"role": "user", "content": "Hello"}]
        )

        with self.assertRaises(HTTPException) as raised:
            await chat(data, request)

        self.assertEqual(raised.exception.status_code, 503)
        self.assertIn("GROQ_API_KEY", raised.exception.detail)
        client.post.assert_not_awaited()

    async def test_completion_response_is_normalized(self) -> None:
        client = AsyncMock()
        client.post.return_value = httpx.Response(
            200,
            json={
                "model": "openai/gpt-oss-20b",
                "choices": [{"message": {"content": '{"answer":"42"}'}}],
            },
            request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions"),
        )
        request = make_request(client=client)
        data = ChatRequest(
            messages=[{"role": "user", "content": "Answer"}],
            format={"type": "object"},
        )

        result = await chat(data, request)

        self.assertEqual(result.model, "openai/gpt-oss-20b")
        self.assertEqual(result.response, '{"answer":"42"}')
        client.post.assert_awaited_once()
        self.assertEqual(
            client.post.await_args.args[0],
            "/chat/completions",
        )

    async def test_completion_response_is_logged_at_info_level(self) -> None:
        client = AsyncMock()
        client.post.return_value = httpx.Response(
            200,
            json={
                "model": "openai/gpt-oss-20b",
                "choices": [{"message": {"content": '{"title":"AI Engineering"}'}}],
            },
            request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions"),
        )
        request = make_request(client=client)
        data = ChatRequest(messages=[{"role": "user", "content": "Create a guide"}])

        with self.assertLogs("uvicorn.error", level="INFO") as logs:
            await chat(data, request)

        self.assertIn('{"title":"AI Engineering"}', logs.output[0])

    async def test_groq_rate_limit_returns_http_429(self) -> None:
        client = AsyncMock()
        client.post.return_value = httpx.Response(
            429,
            json={"error": {"message": "Rate limit reached"}},
            request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions"),
        )
        request = make_request(client=client)
        data = ChatRequest(
            messages=[{"role": "user", "content": "Answer"}]
        )

        with self.assertLogs("uvicorn.error", level="ERROR") as logs:
            with self.assertRaises(HTTPException) as raised:
                await chat(data, request)

        self.assertEqual(raised.exception.status_code, 429)
        self.assertIn("Rate limit reached", raised.exception.detail)
        self.assertIn("Rate limit reached", logs.output[0])


if __name__ == "__main__":
    unittest.main()
