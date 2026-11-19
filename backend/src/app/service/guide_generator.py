from src.app.model.guide import Guide
from src.app.schema.guide_plan import GuidePlan
from src.app.schema.guide_review import GuideReview
from src.app.service.guide import GuideService
from src.app.service.guide_generation import GuideGenerationService
from src.app.service.guide_plan_mapper import to_review_guide
from src.app.service.guide_reviewer import GuideReviewer

DEFAULT_MAX_ATTEMPTS = 3


class GuideGenerationRejectedError(Exception):
    def __init__(
        self,
        guide_plan: GuidePlan,
        final_review: GuideReview,
        attempts: int,
    ) -> None:
        super().__init__("The generated guide did not pass review")
        self.guide_plan = guide_plan
        self.final_review = final_review
        self.attempts = attempts


class GuideGeneratorService:
    def __init__(
        self,
        generation_service: GuideGenerationService,
        reviewer: GuideReviewer,
        guide_service: GuideService,
        *,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        self.generation_service = generation_service
        self.reviewer = reviewer
        self.guide_service = guide_service
        self.max_attempts = max_attempts

    async def generate_guide(self, title: str) -> Guide:
        plan: GuidePlan | None = None
        feedback: str | None = None
        final_review: GuideReview | None = None

        for _ in range(self.max_attempts):
            plan = await self.generation_service.generate(
                title,
                review_feedback=feedback,
                previous_plan=plan,
            )
            final_review = await self.reviewer.review(
                to_review_guide(title, plan),
                title,
            )
            if final_review.approved:
                return await self.guide_service.create_generated_guide(title, plan)

            feedback = final_review.model_dump_json(indent=2)

        if plan is None or final_review is None:
            raise RuntimeError("Guide generation completed without a review")
        raise GuideGenerationRejectedError(plan, final_review, self.max_attempts)
