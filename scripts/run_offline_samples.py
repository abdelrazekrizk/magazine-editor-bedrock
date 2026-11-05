"""Run synthetic sample articles through the deterministic offline workflow."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from magazine_editor.editorial_review import (
    ArticleReviewRequest,
    EditorialReviewWorkflow,
    ReviewResult,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLES_DIR = PROJECT_ROOT / "sample_articles"
RESULTS_PATH = PROJECT_ROOT / "test-results" / "offline-sample-results.json"
SAMPLE_NAMES = (
    "clean_business.json",
    "unsupported_claims.json",
    "grammar_review.json",
    "section_mismatch.json",
)


def main() -> None:
    workflow = EditorialReviewWorkflow()
    results = []
    console_results: list[tuple[str, ReviewResult]] = []

    for name in SAMPLE_NAMES:
        article_data = json.loads(
            (SAMPLES_DIR / name).read_text(encoding="utf-8")
        )
        request = ArticleReviewRequest(
            title=article_data["title"],
            body=article_data["body"],
            section=article_data["section"],
            source_links=article_data.get("source_links", []),
            author=article_data.get("author", "unknown"),
        )
        review_result = workflow.review(request)
        console_results.append((name, review_result))
        results.append(
            {
                "sample": name,
                "mode": "deterministic_offline_heuristics",
                "bedrock_called": False,
                "result": asdict(review_result),
            }
        )

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(
        json.dumps(
            {
                "suite": "magazine_editor_synthetic_samples",
                "mode": "deterministic_offline_heuristics",
                "bedrock_called": False,
                "sample_results": results,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Saved {len(results)} offline sample results to {RESULTS_PATH}")
    for sample_name, review in console_results:
        print(
            f"{sample_name}: {review.final_decision} "
            f"(risk={review.fact_check_risk:.2f}, "
            f"grammar={review.grammar_score:.2f}, "
            f"fit={review.section_fit_score:.2f})"
        )


if __name__ == "__main__":
    main()
