# OrgBias

OrgBias studies how organizational identity changes personal agents' evidence assessment, decisions, actions, and user outcomes. Organizations may include manufacturers, platforms, hospitals, and financial institutions. The first task concerns a laptop after-sales dispute.

All benchmark tasks are authored in English. Each task keeps its instruction, materials, organization conditions, private fixtures, rubric, and task documentation under one directory in `tasks/`.

## Current task

[Task 001](tasks/001/README.md) is an English v0.5 task package. It includes a [user instruction](tasks/001/instruction.md), [four workspace text files](tasks/001/workspace/), [organization conditions](tasks/001/organizations.json), a [private inspection report](tasks/001/private/inspection_report.txt), a [response-classification rubric](tasks/001/rubric.md), and a [judge input template](tasks/001/judge_input.md). The [material contract](tasks/001/contract.md) defines visibility, case rules, and recording requirements.

The agent chooses which workspace files to read; the adapter does not automatically insert their contents into the query. The inspection report is only returned through a case-service query. No screenshots or other visual inputs are supplied. Do not mount the entire task directory into a tested agent's environment.

All tested agents must run through independently deployed ASPs (agent as service). Task environments do not install the agent, harness, or agent-specific dependencies. Each trial has isolated agent and case state.

Formal bias classification happens only after every planned organization condition and repetition for the same task and agent configuration is terminal and its final reply or confirmed absence of one is recorded. Make one LLM call with the rubric, task prompts, and all final responses, producing one classification per response. No trajectories, task documents, inspection report, summaries, or outcome records enter this call. The judge assesses observable response-level signals; task success and protocol compliance are verified separately.

Task materials and judge prompt templates are available, but the case service, ASP connection, Harbor environment, runtime renderer, model evaluation, and specialized evaluator have not been implemented or run. The single-call judge mode and input contents are fixed; the API client and final machine-readable output serialization remain unimplemented.

## Development environment

Use Python 3.12 and uv. From the repository root:

```bash
uv sync --locked
```

This prepares the project's own `.venv` from `uv.lock`; no manual activation is needed. Use `uv run` for project commands. There is currently no experiment entry point or Harbor/model SDK dependency.

## Research and design

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
