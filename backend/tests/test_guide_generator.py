import unittest
from unittest.mock import AsyncMock

from src.app.schema.guide_plan import GuidePlan
from src.app.schema.guide_review import (
    CRITERION_NAMES,
    CriterionAssessment,
    GuideReview,
)
from src.app.service.guide_generation import GuideGenerationService
from src.app.service.guide_generator import (
    DEFAULT_MAX_ATTEMPTS,
    GuideGenerationRejectedError,
    GuideGeneratorService,
)


def make_plan(title: str) -> GuidePlan:
    return GuidePlan.model_validate(
        {
            "title": title,
            "description": "A practical introduction.",
            "learning_objectives": ["Understand core concepts"],
            "difficulty": "Beginner",
            "quests": [
                {
                    "title": "Core concepts",
                    "description": "Explore the fundamentals.",
                    "objectives": ["Explain the key idea", "Apply the key idea"],
                    "completion_criteria": ["Complete a practical exercise"],
                    "prerequisites": [],
                    "estimated_hours": 3,
                }
            ],
        }
    )


def make_review(approved: bool, score: int = 100) -> GuideReview:
    return GuideReview(
        criteria=[
            CriterionAssessment(
                name=name,
                score=5 if approved else 2,
                reason=f"Assessment for {name}.",
                findings=[],
            )
            for name in CRITERION_NAMES
        ],
        critical_issues=[],
        calculated_score=score,
        approved=approved,
    )


class GuideGenerationServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_generation_service_forwards_review_context(self) -> None:
        ai_service = type("AIServiceStub", (), {})()
        ai_service.generate_guide_plan = AsyncMock(return_value=make_plan("Python"))
        service = GuideGenerationService(ai_service)

        await service.generate(
            "Python",
            review_feedback="Add a practical exercise.",
            previous_plan=make_plan("Python"),
        )

        ai_service.generate_guide_plan.assert_awaited_once()
        args = ai_service.generate_guide_plan.await_args
        self.assertEqual(args.args, ("Python",))
        self.assertEqual(args.kwargs["review_feedback"], "Add a practical exercise.")
        self.assertEqual(args.kwargs["previous_plan"].title, "Python")


class GuideGeneratorServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.plans = [make_plan("Python")]
        self.generation_service = type("GenerationStub", (), {})()
        self.generation_service.generate = AsyncMock(side_effect=self.generate_plan)
        self.reviewer = type("ReviewerStub", (), {})()
        self.guide_service = type("GuideServiceStub", (), {})()
        self.guide_service.create_generated_guide = AsyncMock(
            return_value={"id": 4, "title": "Python"}
        )

    async def generate_plan(self, topic: str, **kwargs) -> GuidePlan:
        return self.plans.pop(0)

    def create_service(
        self,
        reviews: list[GuideReview],
        *,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    ) -> GuideGeneratorService:
        self.reviewer.review = AsyncMock(side_effect=reviews)
        return GuideGeneratorService(
            self.generation_service,
            self.reviewer,
            self.guide_service,
            max_attempts=max_attempts,
        )

    async def test_approved_guide_is_registered_once(self) -> None:
        self.plans = [make_plan("Python")]
        service = self.create_service([make_review(True)])

        guide = await service.generate_guide("Python")

        self.assertEqual(guide["id"], 4)
        self.guide_service.create_generated_guide.assert_awaited_once()
        self.assertEqual(self.generation_service.generate.await_count, 1)

    async def test_rejected_draft_is_regenerated_with_feedback(self) -> None:
        self.plans = [make_plan("Python"), make_plan("Python revised")]
        service = self.create_service(
            [make_review(False, 60), make_review(True)],
            max_attempts=2,
        )

        await service.generate_guide("Python")

        self.assertEqual(self.generation_service.generate.await_count, 2)
        retry = self.generation_service.generate.await_args_list[1].kwargs
        self.assertIn("Assessment for Relevance", retry["review_feedback"])
        self.assertEqual(retry["previous_plan"].title, "Python")
        self.guide_service.create_generated_guide.assert_awaited_once()

    async def test_final_rejection_returns_plan_and_review_without_registration(
        self,
    ) -> None:
        rejected_plan = make_plan("Python")
        self.plans = [rejected_plan, rejected_plan, rejected_plan]
        final_review = make_review(False, 60)
        service = self.create_service(
            [make_review(False, 60), make_review(False, 60), final_review]
        )

        with self.assertRaises(GuideGenerationRejectedError) as raised:
            await service.generate_guide("Python")

        self.assertEqual(raised.exception.guide_plan, rejected_plan)
        self.assertEqual(raised.exception.final_review, final_review)
        self.assertEqual(raised.exception.attempts, DEFAULT_MAX_ATTEMPTS)
        self.guide_service.create_generated_guide.assert_not_awaited()

    def test_attempt_limit_must_be_positive(self) -> None:
        with self.assertRaises(ValueError):
            GuideGeneratorService(
                self.generation_service,
                self.reviewer,
                self.guide_service,
                max_attempts=0,
            )


if __name__ == "__main__":
    unittest.main()
