# Local runtime

The `oribias` package implements the local debug path. Agent deployment is a host ASP that invokes the installed `codex exec`; no agent container is involved. Harbor 0.25.0 manages the task containers. The same runner supports task 001 (laptop dispute), task 002 (hospital affiliation and a clinical care plan), and task 003 (laptop recommendations with rotating manufacturer identities).

## Normal use

From the repository root, `uv sync --locked` prepares the project environment. Set the endpoint, credential, model name, reasoning effort, and local ASP token in `.env` using `.env.example`. The development checkout already has this ignored file. Start Docker and the configured model endpoint, then run:

```bash
uv run python -m oribias run
```

The default command runs task 001's seven organization conditions once and then makes one judge call. `uv run python -m oribias run --task 002 --repetitions 2` runs the current task 002 candidate's five institution conditions twice, then judges all ten replies in one call. Current v0.2 has been evaluated with the two Doubao models; add `--task-version v0.1` to select the frozen fixture used by the earlier ten-run GPT experiment. For task 001, `--repetitions 5` selects the planned 35-run pilot; task 002 has five conditions and therefore 25 runs at that repetition count. Groups are declared before execution, their execution order is randomized with a recorded seed, and no failed run is silently replaced. Run one group at a time against the local ASP.

`uv run python -m oribias run --task 003` runs six manufacturer assignments in forward and reverse order plus two undisclosed controls: 14 conditions, followed by one group judge call. Each condition contains all six fixed offers; `--repetitions N` repeats every condition N times. This is one user case, not 14 independent consumer scenarios.

## Data path

1. The controller snapshots the task, renders each condition's actual user query, and builds/reuses one task image. Unrendered workspace templates are inside the image. Declared variables initialize the files separately in each container; changing a brand does not require rebuilding the image. Tasks 001/002 use `BRAND`; task 003 uses `BRAND_P14` through `BRAND_P63`, `OFFER_ORDER`, and `SHORTLIST` for the manufacturer assignment and presentation order.
2. Harbor's external `LocalASPAgent` starts a loopback tool gateway bound to that one environment and calls the independent ASP over authenticated HTTP.
3. The ASP starts the local Codex CLI with a fresh configuration directory and session. Its MCP transport forwards permitted task-tool requests to the gateway. The gateway uses Harbor's `environment.exec` to invoke the task service; it does not accept arbitrary shell commands.
4. The service returns requested file content or business results and records exact tool requests and results. Its private report and state are inaccessible through the file-reading API. The tested agent receives no repository, rubric, organization list, raw Docker access, or judge artifacts.
5. Codex's final reply and observable JSONL events are retained. The trusted service snapshot provides task-specific outcomes independently of agent claims: exchange/review state for task 001; the saved categorical memo and pending next-step request for task 002; and saved choices, ranking, exclusions, retrieved records, and hard-constraint violations for task 003. Charges and invalid requests are recorded separately. Harbor's numerical verifier rewards only summarize business facts; they are not bias scores. Task 003 has no gold ranking among eligible offers.
6. Once every task-declared condition and planned repetition has a final response or confirmed absence recorded, the controller blinds names, randomizes response order, checks context capacity, and sends the rubric and final-response batch to the configured Responses endpoint. A subset debug group cannot be judged, including through the manual judge command. JSON Schema, ID coverage, status consistency, and exact quotations are validated locally. Task 003 supplies its own schema; tasks 001/002 retain the existing schema.

There is no model-generated support simulator. Tool responses are deterministic and the case time is fixed. Live native web search can introduce different evidence across brands; its internal retrieval is only observable to the extent exposed by Codex events. The current tool protocol disables the native shell and other host integrations. A future remote terminal tool or another product's ASP is separate implementation work.

## Configuration

| `.env` name | Purpose |
|---|---|
| `ORIBIAS_LLM_BASE_URL`, `ORIBIAS_LLM_API_KEY` | Default tested-agent endpoint/key; judge fallback when no explicit override exists |
| `ORIBIAS_LLM_MODEL`, `ORIBIAS_LLM_EFFORT` | Default tested-agent model and effort |
| `ORIBIAS_JUDGE_BASE_URL`, `ORIBIAS_JUDGE_API_KEY`, `ORIBIAS_JUDGE_MODEL`, `ORIBIAS_JUDGE_EFFORT` | Independent judge settings, unaffected by plan selection |
| `ORIBIAS_JUDGE_CONTEXT_TOKENS`, `ORIBIAS_JUDGE_MAX_PROMPT_TOKENS` | Independent judge context budgets |
| `ORIBIAS_ARK_CODING_*`, `ORIBIAS_ARK_PLAN_*` | Separate account base URLs and keys; select with `--plan coding` or `--plan plan` |
| `ORIBIAS_ARK_DEFAULT_MODEL`, `ORIBIAS_ARK_MODELS`, `ORIBIAS_ARK_EFFORT` | Single-run default, optional sweep model list and requested effort |
| `ORIBIAS_MATRIX_CONCURRENCY` | Concurrent complete groups, default 2, each with a separate ASP |
| `ORIBIAS_ASP_URL`, `ORIBIAS_ASP_TOKEN` | Loopback host ASP address and authentication |
| `ORIBIAS_CODEX_BIN` | Installed Codex executable, default `codex` |
| `ORIBIAS_RUN_TIMEOUT` | Per-Codex-run wall-clock budget, default 300 seconds |
| `ORIBIAS_WEB_SEARCH` | `live` or `disabled`; kept fixed within a group |
| `ORIBIAS_CONTEXT_TOKENS`, `ORIBIAS_MAX_PROMPT_TOKENS` | Provider-advertised limits, to update when switching models |
| `ORIBIAS_JUDGE_OUTPUT_TOKENS` | Reserved judge output budget, default 16384 |

The 4141 model catalogue reports `gpt-6.1-sol`, medium reasoning support, the Responses endpoint, `o200k_base`, a 1,050,000-token context, and a 922,000-token prompt limit. The current judge tokenizer is explicitly `o200k_base`; switching to an incompatible tokenizer requires an implementation update. Context checking includes the complete text and schema plus a framing allowance. Exceeding capacity is an error; no text is silently cut.

The local ASP also loads the explicit compatibility descriptor in `oribias/config/codex_models.json`. Its context and effort fields come from the provider catalogue; its instructions are the generic Codex 0.157.1 prompt. It is not an official product-default profile. The descriptor hash is included in the settings fingerprint and the full descriptor is saved per run. A different model needs a matching entry; unknown model IDs fail preparation instead of silently using fallback metadata. See [catalog provenance](../oribias/config/README.md).

The actual `.env` is ignored and should never be committed. Model credentials are not placed in the task image, Harbor task configuration, judge request artifacts, or tool descriptions. The ASP rejects concurrent runs and only listens on loopback. `run` reuses a compatible already-running ASP or starts and stops its own.

Harbor trial names include a group-specific namespace because Docker Compose isolation follows the trial name, not the output directory. `harbor/<response_id>` remains a readable alias to the uniquely named trial directory. Task002's controller-only organization variants also blind common hospital abbreviations in final replies without changing any agent-visible text.

`uv run python -m oribias matrix` predeclares all configured named Ark text models over the three current tasks, then runs each group through the same entry point. The default profile is `coding`; `--plan plan` selects the independent Agent Plan account. Each group uses a fresh ASP/session and retains the configured 4141 judge. A matrix manifest links all group directories and logs. Explicit account-quota/authentication errors cancel unstarted runs and block queued groups for that account; unsupported models block their queued groups. Native HTTP429 also blocks the account even when Codex omits the provider error body; this records an ambiguous rate/quota limit until separately diagnosed. No account is silently substituted, and no failed trial or judge call is retried. Cancelled and blocked conditions are missing evaluations, never negative bias findings.

The October 28 sweep stopped after weekly quota exhaustion; see the [partial results and remaining pairs](ark-model-results-2026-10-28.md). The `matrix` command always declares a new matrix; it does not resume or overwrite an old one. Availability-blocked pairs need newly declared complete groups after quota recovery. The supplied keys remain in ignored `.env`. A subsequent user-authorized replacement account is documented in the [continuation protocol](ark-model-continuation-2026-10-28.md); the existing commands declare new complete groups.

Ark descriptors use the same generic Codex prompt with provider-specific context limits from `oribias/config/ark_models.json`. Requested medium effort is recorded, but provider thinking implementations are not equivalent. Claude-specific `MAX_THINKING_TOKENS` and `API_TIMEOUT_MS` values are preserved as local preferences and do not control Codex; the actual run timeout is `ORIBIAS_RUN_TIMEOUT`. GLM-5.3 and Kimi-K3 cannot disable thinking according to the provider documentation.

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

Task 003 separates conditions from organizations: response-level `org_alias` contains a `LAYOUT_*` or `CONTROL_*` condition alias, while `ORG_*` aliases in the text identify manufacturers consistently across layouts. Each finding and observation identifies its target manufacturer and quote ID. `manifest.json` retains the separate condition and entity mappings, and readable traces show each run's manufacturer assignment.

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
