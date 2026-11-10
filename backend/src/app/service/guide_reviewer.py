from pydantic import ValidationError

from src.app.schema.ai import ChatRequest
from src.app.schema.guide import GuideRead
from src.app.schema.guide_review import (
    GuideReview,
    GuideReviewAssessment,
)
from src.app.service.ai import AIService, AIServiceError
from src.app.service.guide_reviewer_prompt import GUIDE_REVIEWER_SYSTEM_PROMPT
from src.app.service.guide_review_validation import (
    GuideReviewValidationError as EvidenceValidationError,
    validate_review_evidence,
)

CRITERION_WEIGHTS = {
    "Relevance": 20,
    "Completeness": 20,
    "Progression": 20,
    "Consistency": 15,
    "Difficulty": 15,
    "Clarity": 10,
}
REVIEW_TEMPERATURE = 0.0
REVIEW_SEED = 42
DEFAULT_MINIMUM_SCORE = 80
DEFAULT_MINIMUM_CRITERION_SCORE = 3


class GuideReviewValidationFailure(AIServiceError):
    def __init__(self, message: str) -> None:
        super().__init__(message, 502)


class GuideReviewer:
    def __init__(
        self,
        ai_service: AIService | None = None,
        *,
        minimum_score: int = DEFAULT_MINIMUM_SCORE,
        minimum_criterion_score: int = DEFAULT_MINIMUM_CRITERION_SCORE,
    ) -> None:
        if not 0 <= minimum_score <= 100:
            raise ValueError("minimum_score must be between 0 and 100")
        if not 0 <= minimum_criterion_score <= 5:
            raise ValueError("minimum_criterion_score must be between 0 and 5")

        self.ai_service = ai_service if ai_service is not None else AIService()
        self.minimum_score = minimum_score
        self.minimum_criterion_score = minimum_criterion_score

    async def review(self, guide: GuideRead, original_request: str) -> GuideReview:
        request = ChatRequest(
            messages=[
                {
                    "role": "system",
                    "content": GUIDE_REVIEWER_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": (
                        f"Original user request:\n{original_request}\n\n"
                        f"Guide to review:\n{guide.model_dump_json()}"
                    ),
                },
            ],
            format=GuideReviewAssessment.model_json_schema(),
            options={"temperature": REVIEW_TEMPERATURE, "seed": REVIEW_SEED},
        )
        response = await self.ai_service.chat(request)
        try:
            assessment = GuideReviewAssessment.model_validate_json(response.response)
        except ValidationError as error:
            raise GuideReviewValidationFailure(
                "AI service returned an invalid guide assessment"
            ) from error

        try:
            validate_review_evidence(guide, assessment)
        except EvidenceValidationError as error:
            raise GuideReviewValidationFailure(
                "AI service returned unverifiable guide review evidence"
            ) from error

        calculated_score = round(
            sum(
                CRITERION_WEIGHTS[criterion.name] * criterion.score / 5
                for criterion in assessment.criteria
            )
        )
        approved = (
            calculated_score >= self.minimum_score
            and all(
                criterion.score >= self.minimum_criterion_score
                for criterion in assessment.criteria
            )
            and not assessment.critical_issues
        )

        return GuideReview(
            criteria=assessment.criteria,
            critical_issues=assessment.critical_issues,
            calculated_score=calculated_score,
            approved=approved,
        )
