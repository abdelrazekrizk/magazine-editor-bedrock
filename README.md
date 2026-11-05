# Magazine Editor — Bedrock Editorial Review

A Python command-line tool that provides advisory editorial feedback on magazine article drafts. It supports a deterministic offline workflow and an explicit Amazon Bedrock-backed workflow. A human editor retains final approval; this tool does not approve or publish articles.

## Requirements

- Python 3.14 or newer
- Windows PowerShell, macOS, or Linux
- For the live review only: Amazon Bedrock access and a configured model

## Install

From the repository root, create a virtual environment and install the project with its development and test dependencies.

Windows PowerShell:

- `python -m venv .venv`
- `& .\.venv\Scripts\python.exe -m pip install -e ".[dev,testing]"`

macOS/Linux:

- `python3 -m venv .venv`
- `./.venv/bin/python -m pip install -e ".[dev,testing]"`

The `magazine-editor-review` command is installed with the package. Equivalent module invocation is `python -m magazine_editor.cli`.

## Offline demo

Run all included deterministic sample articles from the repository root:

- Windows PowerShell: `& .\.venv\Scripts\python.exe -m scripts.run_offline_samples`
- macOS/Linux: `./.venv/bin/python -m scripts.run_offline_samples`

The runner reviews four synthetic examples and writes `test-results/offline-sample-results.json`. It does not load dotenv credentials or call Bedrock. `borderline_section_fit.json` is available as an additional sample but is not included in the default runner.

The local fact-risk, grammar, and section-fit scores are simple heuristics. They do not verify facts, visit source links, or provide reliable proofreading. Use the results only as a demonstration of the local workflow.

## Live Bedrock review

Configure `AWS_BEARER_TOKEN_BEDROCK` and either `BEDROCK_MODEL_ID` or `AI_MODEL` in your process environment or in a local project `.env` file. `AWS_REGION` is optional and defaults to `us-east-1`. Existing process environment values take precedence over dotenv values.

Do not commit `.env` or share its contents. Run one review explicitly:

- Windows PowerShell: `& .\.venv\Scripts\python.exe -m magazine_editor.cli .\sample_articles\clean_business.json`
- macOS/Linux: `./.venv/bin/python -m magazine_editor.cli ./sample_articles/clean_business.json`

A live review sends the selected article text and metadata to Amazon Bedrock, makes three model assessments, and may incur AWS charges. The output is advisory JSON and requires human editorial review. The command performs inference only; it does not deploy to AWS or publish content.

## Tests and lint

From the repository root:

- Windows PowerShell: `& .\.venv\Scripts\python.exe -m pytest tests/ -v --cov`
- macOS/Linux: `./.venv/bin/python -m pytest tests/ -v --cov`
- Ruff: `ruff check magazine_editor scripts tests`

Tests use mocks for model-backed behavior; they do not make real Bedrock requests. The PowerShell helper `scripts/run_pytest.ps1` creates `.venv` if needed, installs the declared development/testing extras, and saves test output under `test-results/`.

## Review workflow

The live CLI accepts a JSON article path, for example `sample_articles/clean_business.json`. It prints an advisory recommendation and findings. Review all suggestions and independently verify claims and sources before making editorial decisions.
