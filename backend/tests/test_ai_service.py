import unittest
from unittest.mock import AsyncMock, patch

import httpx

from src.app.schema.ai import ChatRequest, ChatResponse
from src.app.schema.guide_plan import GuidePlan
from src.app.service.ai import AIService, AIServiceError


class AIServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_invalid_guide_plan_is_retried_with_validation_feedback(self) -> None:
        service = AIService()
        valid_plan = {
            "title": "AI Engineering",
            "description": "A practical guide.",
            "learning_objectives": ["Build an AI application"],
            "difficulty": "Beginner",
            "quests": [
                {
                    "title": "Foundations",
                    "description": "Learn core concepts.",
                    "objectives": ["Explain AI", "Use an AI model"],
                    "completion_criteria": ["Build a small project"],
                    "prerequisites": [],
                    "estimated_hours": 3,
                }
            ],
        }
        service.chat = AsyncMock(
            side_effect=[
                ChatResponse(model="test-model", response='{"title": "incomplete"}'),
                ChatResponse(
                    model="test-model",
                    response=GuidePlan.model_validate(valid_plan).model_dump_json(),
                ),
            ]
        )

        result = await service.generate_guide_plan("Becoming an AI engineer")

        self.assertEqual(result.title, "AI Engineering")
        self.assertEqual(service.chat.await_count, 2)
        retry_request = service.chat.await_args_list[1].args[0]
        self.assertIn("failed validation", retry_request.messages[1].content)
        self.assertIn("Previous response", retry_request.messages[1].content)
        self.assertEqual(
            service.chat.await_args_list[0].args[0].options,
            {"max_completion_tokens": 8192},
        )

    async def test_invalid_guide_plan_after_retry_reports_validation_errors(self) -> None:
        service = AIService()
        service.chat = AsyncMock(
            return_value=ChatResponse(
                model="test-model",
                response='{"title": "incomplete"}',
            )
        )

        with self.assertLogs("src.app.service.ai", level="WARNING") as logs:
            with self.assertRaises(AIServiceError) as raised:
                await service.generate_guide_plan("Becoming an AI engineer")

        self.assertIn("invalid guide plan after retry", str(raised.exception))
        self.assertIn("description", str(raised.exception))
        self.assertEqual(raised.exception.status_code, 502)
        self.assertEqual(service.chat.await_count, 2)
        self.assertIn("response='{\"title\": \"incomplete\"}'", logs.output[0])
        self.assertIn("validation_errors=", logs.output[0])

    async def test_http_error_includes_ai_service_detail(self) -> None:
        response = httpx.Response(
            502,
            json={"detail": "Groq returned status 500"},
            request=httpx.Request("POST", "http://ai-service:8090/chat"),
        )
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.post.return_value = response
        request = ChatRequest(
            messages=[{"role": "user", "content": "Create a guide"}]
        )

        with patch(
            "src.app.service.ai.httpx.AsyncClient",
            return_value=client,
        ):
            with self.assertRaises(AIServiceError) as raised:
                await AIService().chat(request)

        self.assertEqual(raised.exception.status_code, 502)
        self.assertEqual(
            str(raised.exception),
            "AI service returned HTTP 502: Groq returned status 500",
        )

    async def test_rate_limit_status_is_preserved(self) -> None:
        response = httpx.Response(
            429,
            json={"detail": "Groq rate limit exceeded"},
            request=httpx.Request("POST", "http://ai-service:8090/chat"),
        )
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.post.return_value = response
        request = ChatRequest(
            messages=[{"role": "user", "content": "Create a guide"}]
        )

        with patch(
            "src.app.service.ai.httpx.AsyncClient",
            return_value=client,
        ):
            with self.assertRaises(AIServiceError) as raised:
                await AIService().chat(request)

        self.assertEqual(raised.exception.status_code, 429)


if __name__ == "__main__":
    unittest.main()
