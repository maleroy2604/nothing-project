import logging
import os

import httpx
from pydantic import ValidationError

from src.app.schema.ai import ChatRequest, ChatResponse
from src.app.schema.guide_plan import GuidePlan

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are a professional technical learning architect.

Your task is to design structured, progressive and
practical learning guides.

GUIDE DESIGN RULES:

1. Analyse the requested topic and identify its
   fundamental knowledge domains.

2. Determine the appropriate number of quests.
   The number must depend on topic complexity.
   Do not use a fixed number.

3. Organise quests in a logical progression.
   Each quest must build on previous knowledge.

4. Avoid unnecessary fragmentation and overlapping
   quests.

5. Each quest must have:
   - A clear title.
   - A practical description.
   - 2 to 5 measurable learning objectives.
   - Verifiable completion criteria.
   - Estimated learning hours.
   - Prerequisites when applicable.

6. Completion criteria must demonstrate practical
   competence, not simply time spent watching videos.

7. Prefer exercises, implementations, experiments,
   debugging and practical projects.

8. Do not assume the learner is an expert.
   Establish reasonable prerequisites.

9. Do not invent certifications or mandatory courses.

10. Return only JSON matching the supplied schema.
"""


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
                    json=request.model_dump(exclude_none=True),
                )
                response.raise_for_status()
        except httpx.TimeoutException as error:
            raise AIServiceError("AI service request timed out", 504) from error
        except httpx.HTTPStatusError as error:
            message = f"AI service returned HTTP {error.response.status_code}"
            try:
                payload = error.response.json()
            except ValueError:
                payload = None
            if (
                isinstance(payload, dict)
                and isinstance(payload.get("detail"), str)
                and payload["detail"]
            ):
                message += f": {payload['detail']}"
            status_code = (
                error.response.status_code
                if error.response.status_code in (429, 503, 504)
                else 502
            )
            raise AIServiceError(message, status_code) from error
        except httpx.RequestError as error:
            raise AIServiceError("AI service is unavailable", 502) from error

        try:
            return ChatResponse.model_validate(response.json())
        except ValueError as error:
            raise AIServiceError("AI service returned an invalid response", 502) from error

    async def generate_guide_plan(
        self,
        topic: str,
        review_feedback: str | None = None,
        previous_plan: GuidePlan | None = None,
    ) -> GuidePlan:
        user_content = f"Create a learning guide about: {topic}"
        if review_feedback is not None and previous_plan is not None:
            user_content += (
                "\n\nRevise the previous guide to address this reviewer feedback. "
                "Keep sound material, correct the identified issues, and return "
                "the complete revised guide.\n\n"
                f"Previous guide:\n{previous_plan.model_dump_json(indent=2)}\n\n"
                f"Reviewer feedback:\n{review_feedback}"
            )

        previous_response: str | None = None
        validation_errors: list[dict[str, object]] | None = None
        for attempt in range(2):
            attempt_content = user_content
            if previous_response is not None and validation_errors is not None:
                attempt_content += (
                    "\n\nYour previous response failed validation. Correct it and "
                    "return the complete guide as valid JSON only.\n\n"
                    f"Validation errors:\n{validation_errors}\n\n"
                    f"Previous response:\n{previous_response}"
                )

            request = ChatRequest(
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": attempt_content,
                    },
                ],
                format=GuidePlan.model_json_schema(),
                options={"max_completion_tokens": 8192},
            )
            response = await self.chat(request)
            previous_response = response.response
            try:
                return GuidePlan.model_validate_json(response.response)
            except ValidationError as error:
                validation_errors = error.errors(include_url=False)
                logger.warning(
                    "AI service returned an invalid guide plan "
                    "attempt=%s validation_errors=%s response=%r",
                    attempt + 1,
                    validation_errors,
                    response.response,
                )
                if attempt == 1:
                    summary = "; ".join(
                        f"{'.'.join(str(part) for part in issue['loc'])}: "
                        f"{issue['msg']}"
                        for issue in validation_errors
                    )
                    raise AIServiceError(
                        f"AI service returned an invalid guide plan after retry: "
                        f"{summary}",
                        502,
                    ) from error

        raise RuntimeError("Guide plan validation retry completed unexpectedly")
