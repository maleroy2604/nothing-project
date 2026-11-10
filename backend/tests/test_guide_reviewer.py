import json
import unittest
from unittest.mock import AsyncMock

from pydantic import ValidationError

from src.app.schema.ai import ChatResponse
from src.app.schema.guide import GuideRead
from src.app.schema.guide_review import (
    CRITERION_NAMES,
    GuideReviewAssessment,
)
from src.app.service.guide_reviewer import (
    CRITERION_WEIGHTS,
    GuideReviewValidationFailure,
    GuideReviewer,
)


def make_guide() -> GuideRead:
    return GuideRead.model_validate(
        {
            "id": 1,
            "title": "Python Basics",
            "board_column": "backlog",
            "quests": [
                {
                    "id": 10,
                    "guide_id": 1,
                    "position": 1,
                    "title": "Introduction",
                    "description": "Learn variables",
                    "completion_criteria": "Write a short script",
                    "status": "not_started",
                    "steps": [
                        {
                            "id": 100,
                            "quest_id": 10,
                            "position": 1,
                            "title": "Create a variable",
                            "description": "Store and print a value",
                        }
                    ],
                }
            ],
        }
    )


def make_assessment(
    scores: dict[str, int] | None = None,
    *,
    findings: list[dict] | None = None,
    critical_issues: list[dict] | None = None,
) -> dict:
    scores = scores or {name: 5 for name in CRITERION_NAMES}
    findings = findings or []
    return {
        "criteria": [
            {
                "name": name,
                "score": scores[name],
                "reason": f"Assessment for {name}.",
                "findings": findings if name == "Clarity" else [],
            }
            for name in CRITERION_NAMES
        ],
        "critical_issues": critical_issues or [],
    }


def finding(
    *,
    quest_index: int = 0,
    field: str = "title",
    evidence: str = "Introduction",
) -> dict:
    return {
        "quest_index": quest_index,
        "field": field,
        "evidence": evidence,
        "issue": "The title does not describe the learning task.",
        "recommendation": "Use a title that names the task.",
    }


class GuideReviewerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.guide = make_guide()
        self.ai_service = type("AIServiceStub", (), {})()
        self.ai_service.chat = AsyncMock()
        self.reviewer = GuideReviewer(self.ai_service)

    async def review_payload(self, payload: dict):
        self.ai_service.chat.return_value = ChatResponse(
            model="test-model",
            response=json.dumps(payload),
        )
        return await self.reviewer.review(self.guide, "Teach Python basics.")

    async def test_valid_review_response_is_scored_by_python(self) -> None:
        payload = make_assessment()

        review = await self.review_payload(payload)

        self.assertEqual(review.calculated_score, 100)
        self.assertTrue(review.approved)
        self.assertEqual(len(review.criteria), 6)
        chat_request = self.ai_service.chat.await_args.args[0]
        self.assertEqual(chat_request.options, {"temperature": 0.0, "seed": 42})
        self.assertEqual(chat_request.messages[0].role, "system")
        self.assertEqual(chat_request.messages[1].role, "user")
        self.assertIn("Teach Python basics.", chat_request.messages[1].content)
        self.assertNotIn(
            "calculated_score",
            chat_request.format.get("properties", {}),
        )
        self.assertNotIn("approved", chat_request.format.get("properties", {}))

    def test_missing_criterion_is_rejected(self) -> None:
        payload = make_assessment()
        payload["criteria"].pop()

        with self.assertRaises(ValidationError):
            GuideReviewAssessment.model_validate(payload)

    def test_duplicate_criterion_is_rejected(self) -> None:
        payload = make_assessment()
        payload["criteria"][-1]["name"] = payload["criteria"][0]["name"]

        with self.assertRaises(ValidationError):
            GuideReviewAssessment.model_validate(payload)

    def test_criterion_score_outside_range_is_rejected(self) -> None:
        payload = make_assessment()
        payload["criteria"][0]["score"] = 6

        with self.assertRaises(ValidationError):
            GuideReviewAssessment.model_validate(payload)

    async def test_nonexistent_quest_index_is_rejected(self) -> None:
        payload = make_assessment(findings=[finding(quest_index=1)])

        with self.assertRaises(GuideReviewValidationFailure):
            await self.review_payload(payload)

    async def test_nonexistent_field_path_is_rejected(self) -> None:
        payload = make_assessment(findings=[finding(field="steps.1.title")])

        with self.assertRaises(GuideReviewValidationFailure):
            await self.review_payload(payload)

    async def test_evidence_mismatch_is_rejected(self) -> None:
        payload = make_assessment(findings=[finding(evidence="Invented title")])

        with self.assertRaises(GuideReviewValidationFailure):
            await self.review_payload(payload)

    async def test_nested_step_field_evidence_is_validated(self) -> None:
        payload = make_assessment(
            findings=[
                finding(
                    field="steps.0.title",
                    evidence="Create a variable",
                )
            ]
        )

        review = await self.review_payload(payload)

        self.assertEqual(len(review.criteria[-1].findings), 1)

    async def test_weighted_score_is_calculated_correctly(self) -> None:
        scores = dict(zip(CRITERION_NAMES, [5, 4, 3, 2, 1, 0], strict=True))

        review = await self.review_payload(make_assessment(scores))

        expected = round(
            sum(CRITERION_WEIGHTS[name] * scores[name] / 5 for name in CRITERION_NAMES)
        )
        self.assertEqual(review.calculated_score, expected)
        self.assertEqual(review.calculated_score, 57)

    async def test_rejected_when_any_criterion_is_below_threshold(self) -> None:
        scores = {name: 5 for name in CRITERION_NAMES}
        scores["Clarity"] = 2

        review = await self.review_payload(make_assessment(scores))

        self.assertEqual(review.calculated_score, 94)
        self.assertFalse(review.approved)

    async def test_rejected_when_total_score_is_below_threshold(self) -> None:
        scores = {name: 3 for name in CRITERION_NAMES}

        review = await self.review_payload(make_assessment(scores))

        self.assertEqual(review.calculated_score, 60)
        self.assertFalse(review.approved)

    async def test_approved_when_all_requirements_are_satisfied(self) -> None:
        scores = {name: 4 for name in CRITERION_NAMES}

        review = await self.review_payload(make_assessment(scores))

        self.assertEqual(review.calculated_score, 80)
        self.assertTrue(review.approved)

    async def test_critical_issue_prevents_approval(self) -> None:
        payload = make_assessment(critical_issues=[finding()])

        review = await self.review_payload(payload)

        self.assertFalse(review.approved)

    def test_criterion_weights_cover_all_required_criteria(self) -> None:
        self.assertEqual(set(CRITERION_WEIGHTS), set(CRITERION_NAMES))
        self.assertEqual(sum(CRITERION_WEIGHTS.values()), 100)


if __name__ == "__main__":
    unittest.main()
