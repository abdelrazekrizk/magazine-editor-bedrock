"""Command-line entry point for explicit local Bedrock editorial review."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from typing import cast

from .bedrock_review import BedrockEditorialReviewWorkflow, BedrockReviewError
from .editorial_review import ArticleReviewRequest


def _load_request(path: Path) -> ArticleReviewRequest:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("Input must be a JSON object")
    title = payload.get("title")
    body = payload.get("body")
    section = payload.get("section")
    source_links = payload.get("source_links", [])
    author = payload.get("author", "unknown")
    if (
        not isinstance(title, str)
        or not isinstance(body, str)
        or not isinstance(section, str)
        or not isinstance(author, str)
    ):
        raise TypeError("Article fields have invalid types")
    title = cast(str, title)
    body = cast(str, body)
    section = cast(str, section)
    author = cast(str, author)
    if not isinstance(source_links, list) or any(
        not isinstance(link, str) for link in source_links
    ):
        raise ValueError("Source links have invalid types")
    source_links = cast(list[str], source_links)
    return ArticleReviewRequest(
        title=title,
        body=body,
        section=section,
        source_links=source_links,
        author=author,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run a local, Bedrock-backed editorial review. "
            "The result is advisory; "
            "a human editor retains all approval authority."
        )
    )
    parser.add_argument(
        "article_json", type=Path, help="Path to article input JSON"
    )
    args = parser.parse_args(argv)

    try:
        request = _load_request(args.article_json)
        result = BedrockEditorialReviewWorkflow().review(request)
    except BedrockReviewError as exc:
        print(f"Editorial review unavailable: {exc}", file=sys.stderr)
        return 2
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ):
        print("Unable to read valid article JSON input.", file=sys.stderr)
        return 2

    output = asdict(result)
    output["notice"] = (
        "Advisory recommendation only. A human editor must make "
        "the final decision; "
        "this tool does not approve or publish articles."
    )
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
