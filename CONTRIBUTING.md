# Contributing to OrgBias

Help establish what organizational identity does and does not change in personal agents. We welcome replications, alternative explanations, corrections, new cases and well-supported null findings. A useful contribution need not produce a positive bias label.

## Research contributions

Start an issue describing the question, the closest related work, the planned identity manipulation and the observable outcome. For a task contribution, provide English instructions, synthetic or permission-cleared text materials, organization conditions, a deterministic service where possible, categorical evaluation criteria and a clear account of what is held fixed. All task materials belong under `tasks/<id>/`.

Before collecting results, record the task version, model and harness configuration, sampling/repetition plan, order controls, retrieval policy, stopping rule and analysis. Keep prompt exploration separate from confirmation on new cases. Preserve every planned condition, including failures, refusals, missing replies and null findings. Different versions are not repeated samples of the same case.

Report actual actions separately from statements about actions. A recommendation difference is not by itself unjustified treatment; establish the organization link, consider competing explanations, and distinguish statistical effects from user harm. Clinical tasks need appropriate expert validation before clinical claims are made.

The current protocol uses one final-response-only Judge call per terminal group. If proposing another evaluation design, describe it as a new protocol rather than retroactively replacing old labels. Synthetic evaluator examples must remain labeled as authored controls, never as observed agent behavior. Do not silently repair a failed Judge call or replace failed conditions.

## Code and data

Use Python 3.12 and the project's own uv environment:

```bash
uv sync --locked
uv run python scripts/audit_git_privacy.py
uv run python -m unittest discover -s tests -v
uv run python scripts/verify_results.py
```

These checks run locally without production model calls. Live experiments additionally need the configuration described in [the runtime guide](docs/local-runtime.md). Keep agents behind an independent ASP; task containers should contain only the task environment and lightweight tool interfaces. Keep unrelated Python environments unchanged.

Never include credentials, personal customer/patient records, raw browser profiles or third-party documents without redistribution rights. `runs/` and `artifacts/` remain ignored. Public evidence should be an explicit, reviewed export under `results/`, with provenance, hashes, omissions and redactions documented. The existing exporter has a fixed allowlist for the November 1 archive and must not automatically publish new local runs.

You may use a public contact email or a GitHub no-reply address for your commits. Contact addresses intentionally published by their owners are listed in [.privacy-public-emails](.privacy-public-emails); add an address only with its owner's consent. Unlisted email matches request review and are not proof of a leak. The privacy check includes historical commits and requires a full clone. Use the [source-commit mapping](docs/history-commit-map.json) for experimental revisions affected by the November 1 path cleanup.

Commit messages must use Angular style, such as `feat(tasks): add insurance claim scenario` or `docs(results): explain missing judge classifications`. Update documentation and test the paths a new contributor will actually use. Follow [AGENTS.md](AGENTS.md).

Contributions are made under the repository's Apache-2.0 license, subject to preserved third-party rights in [NOTICE](NOTICE). Please cite the underlying papers and datasets, qualify publication status, and describe limitations without promotional claims about novelty or model neutrality.
