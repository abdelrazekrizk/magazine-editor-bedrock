from magazine_editor.editorial_review import (
    ArticleReviewRequest,
    EditorialReviewWorkflow,
)


def test_fact_check_agent_flags_weak_source_article():
    request = ArticleReviewRequest(
        title="The city is secretly paying everyone in cash",
        body=(
            "This article claims the entire city government is paying "
            "everyone in cash without evidence. It sounds very "
            "suspicious and not supported by records."
        ),
        section="News",
        source_links=[],
    )

    workflow = EditorialReviewWorkflow()
    result = workflow.review(request)

    assert result.final_decision in {"revise", "reject"}
    assert result.fact_check_risk >= 0.5


def test_relevance_agent_flags_section_mismatch():
    request = ArticleReviewRequest(
        title="How to reduce inflation in a national economy",
        body=(
            "This article explains macroeconomic policy, inflation, central "
            "banks, and debt cycles in depth."
        ),
        section="Culture",
        source_links=["https://example.com/economics-analysis"],
    )

    workflow = EditorialReviewWorkflow()
    result = workflow.review(request)

    assert result.section_fit_score < 0.7
    assert result.final_decision in {"revise", "reject"}


def test_review_workflow_approves_well_scoped_article():
    request = ArticleReviewRequest(
        title="How local businesses can plan for a calmer holiday season",
        body=(
            "This article explains how local shops can reduce inventory risk, "
            "improve staffing plans, and manage customer demand during the "
            "holiday season."
        ),
        section="Business",
        source_links=[
            "https://example.com/retail-planning",
            "https://example.com/local-market-report",
        ],
    )

    workflow = EditorialReviewWorkflow()
    result = workflow.review(request)

    assert result.final_decision == "approve"
    assert result.grammar_score >= 0.6
    assert result.fact_check_risk <= 0.5
