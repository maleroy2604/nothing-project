import os

import httpx
from pydantic import ValidationError

from src.app.schema.ai import ChatRequest, ChatResponse
from src.app.schema.guide_plan import GuidePlan

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
            raise AIServiceError("AI service returned an error", 502) from error
        except httpx.RequestError as error:
            raise AIServiceError("AI service is unavailable", 502) from error

        try:
            return ChatResponse.model_validate(response.json())
        except ValueError as error:
            raise AIServiceError("AI service returned an invalid response", 502) from error

    async def generate_guide_plan(self, topic: str) -> GuidePlan:
        request = ChatRequest(
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": f"Create a learning guide about: {topic}",
                },
            ],
            format=GuidePlan.model_json_schema(),
        )
        response = await self.chat(request)
        try:
            return GuidePlan.model_validate_json(response.response)
        except ValidationError as error:
            raise AIServiceError("AI service returned an invalid guide plan", 502) from error
