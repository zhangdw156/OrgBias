# Local runtime

The `oribias` package implements the first local debug path. Agent deployment is a host ASP that invokes the installed `codex exec`; no agent container is involved. Harbor 0.25.0 manages the task containers. The same runner supports task 001 (laptop dispute) and task 002 (hospital affiliation and a clinical care plan).

## Normal use

From the repository root, `uv sync --locked` prepares the project environment. Set the endpoint, credential, model name, reasoning effort, and local ASP token in `.env` using `.env.example`. The development checkout already has this ignored file. Start Docker and the configured model endpoint, then run:

```bash
uv run python -m oribias run
```

The default command runs task 001's seven organization conditions once and then makes one judge call. `uv run python -m oribias run --task 002 --repetitions 2` runs task 002's five institution conditions twice, then judges all ten final replies in one call. `--repetitions 5` selects the planned 35-run pilot. Groups are declared before execution, their execution order is randomized with a recorded seed, and no failed run is silently replaced. Run one group at a time against the local ASP.

## Data path

1. The controller snapshots the task, renders each organization's actual user query, and builds/reuses one task image. Unrendered workspace templates are inside the image. `BRAND` initializes four case files separately in each container; changing the brand does not require rebuilding the image.
2. Harbor's external `LocalASPAgent` starts a loopback tool gateway bound to that one environment and calls the independent ASP over authenticated HTTP.
3. The ASP starts the local Codex CLI with a fresh configuration directory and session. Its MCP transport forwards permitted task-tool requests to the gateway. The gateway uses Harbor's `environment.exec` to invoke the task service; it does not accept arbitrary shell commands.
4. The service returns requested file content or business results and records exact tool requests and results. Its private report and state are inaccessible through the file-reading API. The tested agent receives no repository, rubric, organization list, raw Docker access, or judge artifacts.
5. Codex's final reply and observable JSONL events are retained. The trusted service snapshot provides task-specific outcomes independently of agent claims: exchange/review state for task 001, and the saved categorical memo and pending next-step request for task 002, plus charges and blocked requests. Harbor's numerical verifier rewards only summarize those business facts; they are not bias scores.
6. Once every planned final response or confirmed absence is recorded, the controller blinds names, randomizes response order, checks context capacity, and sends the rubric and final-response batch to the configured Responses endpoint. JSON Schema, ID coverage, status consistency, and exact quotations are validated locally.

There is no model-generated support simulator. Tool responses are deterministic and the case time is fixed. Live native web search can introduce different evidence across brands; its internal retrieval is only observable to the extent exposed by Codex events. The current tool protocol disables the native shell and other host integrations. A future remote terminal tool or another product's ASP is separate implementation work.

## Configuration

| `.env` name | Purpose |
|---|---|
| `ORIBIAS_LLM_BASE_URL`, `ORIBIAS_LLM_API_KEY` | Shared host-side model endpoint and credential |
| `ORIBIAS_LLM_MODEL`, `ORIBIAS_LLM_EFFORT` | Exact shared model ID and effort |
| `ORIBIAS_ASP_URL`, `ORIBIAS_ASP_TOKEN` | Loopback host ASP address and authentication |
| `ORIBIAS_CODEX_BIN` | Installed Codex executable, default `codex` |
| `ORIBIAS_RUN_TIMEOUT` | Per-Codex-run wall-clock budget, default 300 seconds |
| `ORIBIAS_WEB_SEARCH` | `live` or `disabled`; kept fixed within a group |
| `ORIBIAS_CONTEXT_TOKENS`, `ORIBIAS_MAX_PROMPT_TOKENS` | Provider-advertised limits, to update when switching models |
| `ORIBIAS_JUDGE_OUTPUT_TOKENS` | Reserved judge output budget, default 16384 |

The 4141 model catalogue reports `gpt-6.1-sol`, medium reasoning support, the Responses endpoint, `o200k_base`, a 1,050,000-token context, and a 922,000-token prompt limit. The current judge tokenizer is explicitly `o200k_base`; switching to an incompatible tokenizer requires an implementation update. Context checking includes the complete text and schema plus a framing allowance. Exceeding capacity is an error; no text is silently cut.

The local ASP also loads the explicit compatibility descriptor in `oribias/config/codex_models.json`. Its context and effort fields come from the provider catalogue; its instructions are the generic Codex 0.157.1 prompt. It is not an official product-default profile. The descriptor hash is included in the settings fingerprint and the full descriptor is saved per run. A different model needs a matching entry; unknown model IDs fail preparation instead of silently using fallback metadata. See [catalog provenance](../oribias/config/README.md).

The actual `.env` is ignored and should never be committed. Model credentials are not placed in the task image, Harbor task configuration, judge request artifacts, or tool descriptions. The ASP rejects concurrent runs and only listens on loopback. `run` reuses a compatible already-running ASP or starts and stops its own.

## Outputs

| Group-relative path | Contents |
|---|---|
| `manifest.json` | Predeclared runs, seed, settings without secrets, software versions, source hashes, image identity, aliases |
| `task_source/`, `initial_workspace/`, `prepared/` | Controller-only source snapshots, rendered materials, and Harbor inputs |
| `readable_traces/README.md` | Clickable index of final replies and exact task-tool timelines |
| `records/<run_id>.json` | Terminal status and full final reply or confirmed absence |
| `harbor/<run_id>/agent/events.jsonl` | Codex's observable events |
| `harbor/<run_id>/agent/case_snapshot.json` | Trusted service state and exact task-tool audit |
| `harbor/<run_id>/agent/stderr.txt` | Codex diagnostics with configured secrets redacted |
| `outcomes.json` | Per-run business outcomes and infrastructure errors |
| `judge_response_ids.json` | Controller-only mapping from neutral judge response IDs to original run IDs |
| `judge/input.json`, `judge/request.json` | Blinded batch and exact API payload, without authentication headers |
| `judge/budget.json`, `judge/raw_response.txt`, `judge/result.json` | Context check, raw provider result, validated classifications |

Judge metadata uses neutral response IDs such as `R0001`; raw run IDs containing a brand never enter the judge input. `judge/implementation.json` records the judge implementation hash and non-secret settings separately from the agent-run manifest.

Final-only classification cannot verify reading, actual execution, correctness of completion claims, or absence of process bias. Business facts are separate. Final-claim accuracy, final-text follow-up questions, and language compliance still require review; the service does not pretend to verify them automatically. No final response is synthesized from progress messages.

To open recorded tool actions without reading JSONL, use the generated `readable_traces/README.md`. For an older group, generate this view with `uv run python -m oribias traces runs/<group>`; this makes no model calls. The view links the native events for search or harness activity that is not part of the task-tool timeline.

Frozen tasks can be selected with `--task-version v0.6` for task 001, or `--task 002 --task-version v0.1` for the medical task. `--deadline 2026-10-27T21:50:00+08:00` prevents starting agent runs or a judge call when their reserved budget no longer fits. Not-started conditions remain explicit cancelled records; a skipped judge is reported, not silently counted as a negative result.

## Focused debugging

For a single-condition connectivity check without a bias judgment:

```bash
uv run python -m oribias run --org lenovo --no-judge
```

To collect a whole group for inspection before judging, use `run --no-judge`, then `judge runs/<group>` once. A `call_started.json` marker prevents a second call even if the first produced invalid JSON or a network failure. Keep the failed group as evidence; repair the implementation and create a new explicitly identified debug group instead of silently retrying its judgment. An uncertain ASP response blocks group judgment.

For an independently managed local ASP, use `uv run python -m oribias serve`; ordinary `run` does not require this extra step.

## Local verification

```bash
uv run python -m unittest discover -s tests -v
```

These are deterministic local checks of service transitions, authorization, state isolation, file visibility, and judge preparation/validation. They do not execute model inference. Real experiment results and their limitations are recorded separately.
