from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

CriterionName = Literal[
    "Relevance",
    "Completeness",
    "Progression",
    "Consistency",
    "Difficulty",
    "Clarity",
]

CRITERION_NAMES: tuple[str, ...] = (
    "Relevance",
    "Completeness",
    "Progression",
    "Consistency",
    "Difficulty",
    "Clarity",
)


class ReviewFinding(BaseModel):
    quest_index: int = Field(
        ge=0,
        description="Zero-based index of the quest containing the issue.",
    )
    field: str = Field(
        min_length=1,
        description=(
            "Dot-separated path to a text field, such as 'title', "
            "'completion_criteria', or 'steps.0.description'."
        ),
    )
    evidence: str = Field(
        min_length=1,
        description="Exact text copied from the referenced guide field.",
    )
    issue: str = Field(min_length=1, description="The identified problem.")
    recommendation: str = Field(
        min_length=1,
        description="A specific correction for the identified problem.",
    )


class CriterionAssessment(BaseModel):
    name: CriterionName
    score: int = Field(ge=0, le=5)
    reason: str = Field(min_length=1)
    findings: list[ReviewFinding]


class _GuideAssessmentBase(BaseModel):
    criteria: Annotated[
        list[CriterionAssessment],
        Field(min_length=len(CRITERION_NAMES), max_length=len(CRITERION_NAMES)),
    ]
    critical_issues: list[ReviewFinding]

    @model_validator(mode="after")
    def require_each_criterion_once(self) -> "_GuideAssessmentBase":
        names = [criterion.name for criterion in self.criteria]
        duplicates = sorted({name for name in names if names.count(name) > 1})
        missing = sorted(set(CRITERION_NAMES) - set(names))
        if duplicates or missing:
            details = []
            if missing:
                details.append(f"missing criteria: {', '.join(missing)}")
            if duplicates:
                details.append(f"duplicate criteria: {', '.join(duplicates)}")
            raise ValueError("; ".join(details))
        return self


class GuideReviewAssessment(_GuideAssessmentBase):
    model_config = ConfigDict(extra="forbid")


class GuideReview(_GuideAssessmentBase):
    calculated_score: int = Field(ge=0, le=100)
    approved: bool
