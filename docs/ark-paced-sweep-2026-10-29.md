# Paced Ark sweep and monitoring, October 29, 2026

The user authorized continuing the remaining evaluations and actively monitoring them. Use the existing replacement Coding Plan account; keep the fixed Judge at local4141, `gpt-6.1-sol`, medium. The [job list](ark-paced-jobs-2026-10-29.json) declares exactly 41 remaining model/task pairs and 366 new conditions. Earlier partial groups, failed calls and the four complete Pro/Lite groups remain unchanged. No failed condition is patched in place. These new groups are distinct observations.

**Execution result:** this matrix stopped at11:24 Beijing time after the Kimi group's fixed Judge returned HTTP500. All15 agent runs and77 upstream requests succeeded; ten replies have validated no_observed_signal classifications and five remain unclassified. The38 queued groups were blocked. No run remains active; the monitor was deleted after observing termination. See the [final partial-result report](ark-paced-results-2026-10-29.md).

## Execution changes fixed before launch

A host-only HTTP relay forwards the original Responses request body unchanged, including tools and streaming. A shared file lock enforces at least **10 seconds between upstream request starts**, across conditions and ASP processes. It does not retry requests, change models, switch credentials, or modify final responses. It is not part of any task Docker image. Only the configured model and Responses endpoint are exposed, with a local random bearer token; the cloud credential remains on the host.

The interval is a conservative experimental setting, not a documented provider allowance or guarantee that burst protection has cleared. Group concurrency is one. The agent wall-clock timeout increases from 300 to **900 seconds** to include deliberate pacing waits; elapsed times from these groups are not directly comparable to earlier runs. The timeout, interval and state path are recorded in public settings and fingerprints. Task versions, facts, tools, rubrics, generic Codex prompt, requested medium effort and native live-search setting remain unchanged. The Judge's model, credentials, budget and single-call rule remain unchanged.

Each run preserves `agent/provider_requests.json` with request hash, start time, waiting time, HTTP status, request ID and any redacted error body. These records and trusted state remain outside the Judge input. This captures specific errors such as `RequestBurstTooFast` when native Codex hides the provider body.

The order prioritizes task002 across the remaining models, then task001, then task003. GLM-5.3 is first because its endpoint compatibility was previously demonstrated. Every pending pair remains declared; the order is not chosen from new outcome labels. Model-level rejections block later groups for that model. Account-level limits and fixed-Judge HTTP401/403/429/5xx stop queued groups. Missing responses and invalid Judge outputs remain explicit; there are no automatic trial, request or Judge repair retries.

## Launch and actual progress

From the repository root, with the already-configured ignored `.env`:

```bash
uv run python -m oribias matrix --jobs-file docs/ark-paced-jobs-2026-10-29.json
```

This declares a fresh matrix and runs the listed pairs once. It does not resume old group IDs. On this development machine, the owned run is also protected from idle sleep for its lifetime. The authoritative active-matrix pointer is `runs/active-paced.json`; open the referenced `manifest.json` for group paths, status, process IDs and heartbeat. Read each group's `readable_traces/README.md` after its terminal aggregation. A completed matrix job does not imply every condition produced a reply or a valid classification; inspect per-run records and Judge artifacts.

## Monitoring

The matrix writes a heartbeat every15 seconds and records controller and group process IDs. An independent Codex scheduled monitor will inspect the active pointer, heartbeat, process liveness, record progress, provider errors and Judge status every10 minutes. It should stay quiet during normal operation and notify on completion, a new failure/block, a stalled run, or a new validated bias finding. It must not infer weekly quota exhaustion from an unqualified HTTP429.

For a confirmed stall or unhandled availability failure, the monitor can write the matrix's `stop.json` containing `code`, `scope` and `message`; the controller stops dispatch and active groups cancel unstarted conditions at the next boundary. In-flight requests retain their own terminal record. A run can legitimately take up to900 seconds plus orchestration time, so a fresh heartbeat alone is not proof of progress, and a short quiet period is not a stall. Check record/log timestamps and the shared pacing timestamp; confirm any suspected stall before intervening. Do not terminate unrelated processes. No automatic inference restart or failed-Judge re-call is authorized by the monitor protocol.

The scheduled monitor runs locally and requires the Codex app and this machine to remain available. See [official scheduled-task documentation](https://learn.chatgpt.com/docs/automations?surface=app). Its configured task ID and the active matrix are stored locally after creation; live status is not inferred from this registration document.

## Verification before launch

43 deterministic local tests passed, including real local HTTP transport for streaming, unchanged request bodies, shared pacing across two relays, error preservation without retries, authentication and cancellation of waiting requests. Scheduling tests use fake subprocesses and verify exact job pairs and fixed-Judge availability stops. These checks are not external model inference. Live execution under pacing and its classifications are reported from the new matrix artifacts as they become available.
