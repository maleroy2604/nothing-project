from src.app.schema.guide import GuideRead
from src.app.schema.guide_review import GuideReviewAssessment, ReviewFinding


class GuideReviewValidationError(ValueError):
    pass


def validate_review_evidence(
    guide: GuideRead,
    assessment: GuideReviewAssessment,
) -> None:
    findings = [
        finding
        for criterion in assessment.criteria
        for finding in criterion.findings
    ]
    findings.extend(assessment.critical_issues)

    for finding in findings:
        _validate_finding(guide, finding)


def _validate_finding(guide: GuideRead, finding: ReviewFinding) -> None:
    if finding.quest_index >= len(guide.quests):
        raise GuideReviewValidationError(
            f"Finding references non-existent quest index {finding.quest_index}"
        )

    value: object = guide.quests[finding.quest_index].model_dump()
    for segment in finding.field.split("."):
        if isinstance(value, dict) and segment in value:
            value = value[segment]
        elif isinstance(value, list) and segment.isdecimal():
            index = int(segment)
            if index >= len(value):
                raise GuideReviewValidationError(
                    f"Finding references non-existent field '{finding.field}'"
                )
            value = value[index]
        else:
            raise GuideReviewValidationError(
                f"Finding references non-existent field '{finding.field}'"
            )

    if not isinstance(value, str):
        raise GuideReviewValidationError(
            f"Finding field '{finding.field}' does not contain text"
        )
    if finding.evidence != value:
        raise GuideReviewValidationError(
            f"Finding evidence does not exactly match field '{finding.field}' "
            f"on quest index {finding.quest_index}"
        )
