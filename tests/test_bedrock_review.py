from types import SimpleNamespace

import pytest

from magazine_editor import bedrock_review
from magazine_editor.bedrock_review import (
    BedrockConfig,
    BedrockConfigurationError,
    BedrockEditorialReviewWorkflow,
    BedrockReviewError,
    load_bedrock_config,
)
from magazine_editor.editorial_review import ArticleReviewRequest

ARTICLE = ArticleReviewRequest(
    title="Local shops prepare for the holiday season",
    body=(
        "Local shops reviewed staffing and inventory plans for the holiday "
        "season."
    ),
    section="Business",
    source_links=["https://example.test/retail-report"],
    author="Test Writer",
)


def test_configuration_requires_bedrock_bearer_token_without_echoing_it():
    with pytest.raises(BedrockConfigurationError) as error:
        load_bedrock_config(environ={"BEDROCK_MODEL_ID": "test-model"})

    assert "AWS_BEARER_TOKEN_BEDROCK" in str(error.value)
    assert "test-model" not in str(error.value)


def test_configuration_uses_model_fallback_and_default_region():
    config = load_bedrock_config(
        environ={
            "AWS_BEARER_TOKEN_BEDROCK": "test-only-token",
            "AI_MODEL": "fallback-model",
        }
    )

    assert config == BedrockConfig(
        model_id="fallback-model",
        region="us-east-1",
        api_key="test-only-token",
    )
    assert "test-only-token" not in repr(config)


def test_configuration_requires_a_model_id_or_fallback():
    with pytest.raises(BedrockConfigurationError) as error:
        load_bedrock_config(environ={"AWS_BEARER_TOKEN_BEDROCK": "test-token"})

    assert "BEDROCK_MODEL_ID or AI_MODEL" in str(error.value)
    assert "test-token" not in str(error.value)


def test_configuration_prefers_bedrock_model_id_and_configured_region():
    config = load_bedrock_config(
        environ={
            "AWS_BEARER_TOKEN_BEDROCK": "test-only-token",
            "AWS_REGION": "us-west-2",
            "BEDROCK_MODEL_ID": "primary-model",
            "AI_MODEL": "fallback-model",
        }
    )

    assert config == BedrockConfig(
        model_id="primary-model",
        region="us-west-2",
        api_key="test-only-token",
    )


def test_dotenv_values_are_fallbacks_to_process_environment(monkeypatch):
    keys = (
        "AWS_BEARER_TOKEN_BEDROCK",
        "BEDROCK_MODEL_ID",
        "AI_MODEL",
        "AWS_REGION",
    )
    for key in keys:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("AWS_BEARER_TOKEN_BEDROCK", "shell-only-token")

    def fake_load_dotenv(*, override):
        assert override is False
        bedrock_review.os.environ.setdefault(
            "AWS_BEARER_TOKEN_BEDROCK", "dotenv-only-token"
        )
        bedrock_review.os.environ.setdefault(
            "BEDROCK_MODEL_ID", "dotenv-model"
        )
        bedrock_review.os.environ.setdefault("AWS_REGION", "eu-west-1")

    def fake_import(name):
        assert name == "dotenv"
        return SimpleNamespace(load_dotenv=fake_load_dotenv)

    monkeypatch.setattr(bedrock_review, "import_module", fake_import)

    config = load_bedrock_config()

    assert config.api_key == "shell-only-token"
    assert config.model_id == "dotenv-model"
    assert config.region == "eu-west-1"


def test_strands_factory_passes_bedrock_token_without_logging_it(monkeypatch):
    calls = []

    class ModelStub:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class AgentStub:
        def __init__(self, *, model, system_prompt, callback_handler):
            calls.append((model, system_prompt, callback_handler))

        def __call__(self, prompt):
            raise AssertionError(
                "Mock agent should not be invoked in this test"
            )

    def fake_import(name):
        if name == "strands":
            return SimpleNamespace(Agent=AgentStub)
        if name == "strands.models":
            return SimpleNamespace(BedrockModel=ModelStub)
        raise AssertionError(f"Unexpected import: {name}")

    monkeypatch.setattr(bedrock_review, "import_module", fake_import)
    config = BedrockConfig(
        model_id="test-model",
        region="us-east-1",
        api_key="test-only-token",
    )

    BedrockEditorialReviewWorkflow(config)

    assert len(calls) == 3
    assert all(
        model.kwargs
        == {
            "model_id": "test-model",
            "region_name": "us-east-1",
            "api_key": "test-only-token",
        }
        for model, _, callback_handler in calls
    )
    assert all(callback_handler is None for _, _, callback_handler in calls)
    assert "test-only-token" not in repr(config)


def test_workflow_dispatches_three_agents_and_aggregates_advisory_result():
    responses = {
        "fact_source_risk": (
            '{"risk": 0.2, "findings": ["One source supplied."]}'
        ),
        "grammar": '{"score": 0.4, "findings": ["Review wording."]}',
        "section_relevance": '{"score": 0.9, "findings": ["Fits business."]}',
    }
    dispatched = []

    def factory(role, config):
        assert config.model_id == "mock-model"
        dispatched.append(role)
        return lambda prompt: _check_prompt_and_return(
            prompt, role, responses[role]
        )

    workflow = BedrockEditorialReviewWorkflow(
        BedrockConfig(
            model_id="mock-model",
            region="us-east-1",
            api_key="test-only-token",
        ),
        agent_factory=factory,
    )
    result = workflow.review(ARTICLE)

    assert dispatched == ["fact_source_risk", "grammar", "section_relevance"]
    assert result.recommendation == "recommend_revision"
    assert result.human_approval_required is True
    assert result.grammar_findings == ["Review wording."]
    assert not hasattr(result, "publish")


def _check_prompt_and_return(prompt, role, response):
    assert role in prompt
    assert "untrusted" in prompt
    assert ARTICLE.title in prompt
    return response


def test_workflow_parses_strands_message_content_and_holds_high_risk_article():
    responses = {
        "fact_source_risk": SimpleNamespace(
            message={
                "content": [
                    {
                        "text": (
                            '```json\n{"risk": 0.9, '
                            '"findings": ["Unsupported claim."]}\n```'
                        )
                    }
                ]
            }
        ),
        "grammar": '{"score": 0.9, "findings": []}',
        "section_relevance": (
            '{"score": 0.3, "findings": ["Section mismatch."]}'
        ),
    }
    workflow = BedrockEditorialReviewWorkflow(
        BedrockConfig(
            model_id="mock-model",
            region="us-east-1",
            api_key="test-only-token",
        ),
        agent_factory=lambda role, config: lambda prompt: responses[role],
    )

    result = workflow.review(ARTICLE)

    assert result.recommendation == "hold_for_editor"
    assert result.fact_check_risk == 0.9
    assert result.fact_findings == ["Unsupported claim."]


def test_malformed_model_result_fails_with_safe_error():
    workflow = BedrockEditorialReviewWorkflow(
        BedrockConfig(
            model_id="mock-model",
            region="us-east-1",
            api_key="test-only-token",
        ),
        agent_factory=lambda role, config: lambda prompt: (
            "not-json private-token"
        ),
    )

    with pytest.raises(BedrockReviewError) as error:
        workflow.review(ARTICLE)

    assert "Unable to parse" in str(error.value)
    assert "private-token" not in str(error.value)


def test_model_exception_is_sanitized():
    workflow = BedrockEditorialReviewWorkflow(
        BedrockConfig(
            model_id="mock-model",
            region="us-east-1",
            api_key="test-only-token",
        ),
        agent_factory=lambda role, config: lambda prompt: (
            _raise_secret_error()
        ),
    )

    with pytest.raises(BedrockReviewError) as error:
        workflow.review(ARTICLE)

    assert "model review failed" in str(error.value)
    assert "secret-value" not in str(error.value)


def _raise_secret_error():
    raise RuntimeError("request failed with secret-value")
