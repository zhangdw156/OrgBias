# OrgBias

OrgBias studies how organizational identity changes personal agents' evidence assessment, decisions, actions, and user outcomes. Organizations may include manufacturers, platforms, hospitals, and financial institutions. The first task concerns a laptop after-sales dispute.

All benchmark tasks are authored in English. Each task keeps its instruction, materials, organization conditions, private fixtures, rubric, and task documentation under one directory in `tasks/`.

## Tasks

[Task 001](tasks/001/README.md) is an English v0.8 task package. It includes a [user instruction](tasks/001/instruction.md), [four workspace text files](tasks/001/workspace/), [organization conditions](tasks/001/organizations.json), a [private inspection report](tasks/001/private/inspection_report.txt), a [response-classification rubric](tasks/001/rubric.md), and a [judge input template](tasks/001/judge_input.md). The [material contract](tasks/001/contract.md) defines visibility, case rules, and recording requirements.

[Task 002](tasks/002/README.md) is a hospital-affiliation extension: identical endocrine records and a disputed fatigue interpretation are signed by four hospitals or an undisclosed source. Current v0.2 has now been run in complete groups with Doubao Pro and Lite; the earlier ten GPT runs used frozen v0.1. The agent records a care memo and chooses one simulated next-step request. The task fixes clinician credentials, access and fees. No real medication or appointments are involved.

[Task 003](tasks/003/README.md) compares recommendations over six fixed synthetic laptop offers with Lenovo, Dell, HP, ASUS, Acer and CHUWI identities. Six assignments in two presentation orders plus two undisclosed controls make 14 conditions. The agent retrieves records, ranks offers and saves a recommendation. Run it with `uv run python -m oribias run --task 003`. Browser sources and validation limits are kept in the task directory.

Its [first complete group](tasks/003/results/2026-10-28-first-group.md) finished all 14 runs and one Judge call: every run selected P14 first, P28 as backup, and the same full ranking and exclusions. All 14 final replies were classified as `no_observed_signal`. This is a negative result for one fixed case and agent configuration, not proof of general neutrality.

The agent chooses which workspace files to read; the adapter does not automatically insert their contents into the query. In task 001, the inspection report is only returned through a case-service query; task 002 similarly exposes its detailed consultation note through a tool. No screenshots or other visual inputs are supplied. Do not mount the entire task directory into a tested agent's environment.

All tested agents must run through independently deployed ASPs (agent as service). Task environments do not install the agent, harness, or agent-specific dependencies. Each trial has isolated agent and case state.

Formal bias classification happens only after every planned organization condition and repetition for the same task and agent configuration is terminal and its final reply or confirmed absence of one is recorded. Make one LLM call with the rubric, task prompts, and all final responses, producing one classification per response. No trajectories, task documents, inspection report, summaries, or outcome records enter this call. The judge assesses observable response-level signals; task success and protocol compliance are verified separately.

The first local implementation is in [oribias/](oribias/): organization scheduling, rendering, an ASP wrapping the **locally installed Codex CLI**, a Harbor external-agent adapter, and a single-call judge. Docker runs only the task environment and deterministic case service. There is no Codex Dockerfile or agent-container deployment in this version. A specialized trained evaluator remains future work.

## Development environment

Use Python 3.12 and uv. From the repository root:

```bash
uv sync --locked
```

This prepares the project's own `.venv` from `uv.lock`; no manual activation is needed. Local Codex and a working Docker daemon must already be installed.

The current version leaves fault causation unresolved, asks whether the user's suspicion of blame shifting is justified, requests service-trust advice, and asks the agent to choose one free review route first. Earlier task versions remain under `tasks/001/versions/`. See the [bounded iteration plan](docs/task001-iteration-plan-2026-10-27.md).

## Local debug experiment

Configure the provider URL, key, model, and ASP token in `.env`, using [.env.example](.env.example) for a new checkout. The development machine's ignored `.env` retains `http://localhost:4141/v1`, `gpt-6.1-sol`, and `medium` as the default agent. Separate `ORIBIAS_JUDGE_*` settings pin the rubric judge to that GPT configuration when an Ark plan changes the tested model. Credentials stay on the host.

For all 15 named text models in the pinned Ark catalogue across tasks 001/002/003, use `uv run python -m oribias matrix`. This schedules 45 complete groups (390 conditions once), with independent ASP ports and at most two groups concurrently. A single-model group can be run with `uv run python -m oribias run --task 003 --plan coding --model glm-5.3`. Both commands retain the local Codex harness. See the [Ark sweep protocol](docs/ark-model-sweep-2026-10-28.md) for availability, thinking-mode and comparability limits.

The [October 29 paced continuation](docs/ark-paced-sweep-2026-10-29.md) adds a shared 10-second interval between Ark requests, a recorded 900-second agent wall-clock limit and scheduled monitoring. Its exact 41-pair job list excludes the four previously complete pairs. Current execution status is read from `runs/active-paced.json` and its referenced matrix manifest.

The [October 28 Ark result](docs/ark-model-results-2026-10-28.md) is **partial**: 59 conditions started, 35 final replies, 24 HTTP 429 failures, and 331 unstarted conditions after both accounts exhausted weekly quota. All 35 replies were classified as `no_observed_signal`; missing replies were classified as `no_response`. Only Pro/Lite tasks001/002 have full response coverage. The [pending list](docs/ark-model-pending-2026-10-28.json) records 41 model/task pairs still needing complete coverage. The replacement-account continuation also stopped after HTTP429; a later check identified `RequestBurstTooFast`. It added four classified Seed Evolving replies and two Mini replies whose Judge calls failed, with no new full-coverage groups. See the [current result and rate-limit diagnosis](docs/ark-model-serial-results-2026-10-28.md). That October 28 attempt is terminal; the October 29 continuation is recorded separately.

From the repository root:

```bash
uv run python -m oribias run
```

The default task 001 command builds/reuses one task image, automatically starts a local ASP when needed, and runs all seven conditions once in randomized order through Harbor. For task 002, use `uv run python -m oribias run --task 002`; its declared group has five conditions. Each run has a new task container, case state, Codex configuration directory, and session. After the whole group terminates, the judge receives all final replies in one call. This is a **seven-run debug group**, not the planned 35-run pilot. Use `--repetitions 5` for that pilot.

The four case files live in the task's `/workspace` and are accessed through MCP file tools. They are never automatically inserted into the user prompt. The native Codex shell, host skills, plugins, and memory are disabled for this controlled task; native web search is enabled by default. This is a documented local Codex configuration, not an untouched product-default comparison. The protocol prevents interactive approval waits and instructs the agent not to ask questions; a question written in its final reply remains a possible violation, not something the runner rewrites.

Each group is saved under `runs/<group>/`. See [the local runtime guide](docs/local-runtime.md) for artifacts, subset debugging, and validation limits. The program does not retry failed agent runs or judge outputs automatically.

The [first real debug group](docs/local-debug-2026-10-27.md) completed seven Codex runs and one judge call: all seven exchange applications were approved, and all seven final replies were classified as `no_observed_signal`. This small engineering check is not evidence that the agent is free of organizational bias.

The October 27 laptop groups (14 runs) and clinical v0.1 group (10 runs) all returned `no_observed_signal`. The clinical v0.1 material included a potential debiasing cue; v0.2 removes it and was subsequently evaluated with the two Doubao models in the October 28 sweep. These are limited negative findings, not proof of unbiased agents.

The bounded exploration and hospital extension are documented in the [iteration report](docs/bounded-iteration-report-2026-10-27.md), with a [machine-readable result extract](docs/iteration-results-2026-10-27.json).

## Research and design

- [Four-paper task-design review](docs/four-paper-task-design-review-2026-10-27.md): original methods, author-code checks, current design limits, and how to test for small or absent organizational effects.
- [Document index](docs/README.md): project research and engineering notes.
- [Research plan](docs/research-plan.md): objectives, accepted decisions, and experiment sequence.
- [Engineering design](docs/engineering-design.md): ASP integration, Harbor interfaces, unattended execution, and group aggregation.
- [Agent/task deployment review](docs/agent-task-deployment-review.md): independent services, task environments, and official framework implementations.
- [Laptop scenario research](docs/laptop-orgbias-pilot-research.md): source cases, candidate disputes, and evidence limits.
- [Personal-agent literature review](docs/personal-agent-orgbias-review.md): directly related and adjacent research.

## Contributions

Follow [AGENTS.md](AGENTS.md). Commit messages must use Angular style, for example:

```text
feat(tasks): add laptop warranty dispute task
docs(rubric): clarify evidence classification rules
```
