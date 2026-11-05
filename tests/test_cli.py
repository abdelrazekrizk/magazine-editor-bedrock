import json

from magazine_editor import cli
from magazine_editor.bedrock_review import (
    BedrockConfigurationError,
    BedrockReviewResult,
)


def test_cli_reviews_article_and_prints_advisory_result(
    tmp_path, monkeypatch, capsys
):
    article_path = tmp_path / "article.json"
    article_path.write_text(
        json.dumps(
            {
                "title": "Local shops prepare for the holidays",
                "body": "Local businesses are planning seasonal inventory.",
                "section": "Business",
            }
        ),
        encoding="utf-8",
    )
    result = BedrockReviewResult(
        fact_check_risk=0.2,
        grammar_score=0.9,
        section_fit_score=0.8,
        recommendation="recommend_approval",
    )

    class WorkflowStub:
        def review(self, request):
            assert request.title == "Local shops prepare for the holidays"
            return result

    monkeypatch.setattr(cli, "BedrockEditorialReviewWorkflow", WorkflowStub)

    exit_code = cli.main([str(article_path)])

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output["recommendation"] == "recommend_approval"
    assert output["human_approval_required"] is True
    assert output["notice"].endswith(
        "this tool does not approve or publish articles."
    )


def test_cli_reports_invalid_article_without_calling_bedrock(
    tmp_path, monkeypatch, capsys
):
    article_path = tmp_path / "invalid.json"
    article_path.write_text('{"title": 123}', encoding="utf-8")

    def fail_if_called():
        raise AssertionError("Invalid input must not initialize Bedrock")

    monkeypatch.setattr(cli, "BedrockEditorialReviewWorkflow", fail_if_called)

    exit_code = cli.main([str(article_path)])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == ""
    assert "Unable to read valid article JSON input." in captured.err
    assert "123" not in captured.err


def test_cli_sanitizes_configuration_errors(tmp_path, capsys, monkeypatch):
    article_path = tmp_path / "article.json"
    article_path.write_text(
        '{"title":"Test","body":"Body","section":"Business"}',
        encoding="utf-8",
    )

    class WorkflowStub:
        def __init__(self):
            raise BedrockConfigurationError(
                "Missing required configuration: AWS_BEARER_TOKEN_BEDROCK."
            )

    monkeypatch.setattr(
        cli, "BedrockEditorialReviewWorkflow", WorkflowStub
    )
    exit_code = cli.main([str(article_path)])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "AWS_BEARER_TOKEN_BEDROCK" in captured.err
    assert "private-token" not in captured.err
