# Synthetic editorial-review samples

These JSON files are fictional inputs for the magazine-editor review workflow. Any `example.test` links are placeholders, not real sources. Model assessments are advisory and are not factual verification.

## Included samples

- `clean_business.json` — on-topic business article with placeholder source links
- `unsupported_claims.json` — intentionally fictional unsupported-news claim
- `grammar_review.json` — deliberately error-prone writing
- `section_mismatch.json` — economics content assigned to Culture
- `borderline_section_fit.json` — mixed arts and business topic

## Offline demo

From the repository root, run `& .\.venv\Scripts\python.exe -m scripts.run_offline_samples` in Windows PowerShell, or `./.venv/bin/python -m scripts.run_offline_samples` on macOS/Linux.

The runner processes four samples and writes results to `test-results/offline-sample-results.json`. It uses deterministic local heuristics only: it does not read dotenv credentials or call Bedrock. `borderline_section_fit.json` is available for manual exploration and is not included in the default run.

The heuristic grammar score is a simplistic placeholder, not a proofreading model. For example, an intentionally incorrect sample may still receive a high score.

## Optional live Bedrock review

From the repository root, run one sample at a time with the model-backed CLI, for example:

`& .\.venv\Scripts\python.exe -m magazine_editor.cli .\sample_articles\clean_business.json`

This sends the selected article and metadata to Amazon Bedrock and may incur AWS charges. Configure credentials locally, never commit `.env`, and keep final editorial approval with a human. The CLI performs inference only; it does not publish articles or deploy AWS resources.
