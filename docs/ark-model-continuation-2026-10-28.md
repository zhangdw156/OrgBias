# Ark sweep continuation with a replacement Coding Plan account

Registered on October 28, 2026 after the user supplied a replacement Coding Plan credential and described its quota as five times larger. The quota multiplier is user-provided, not independently measured. The credential is stored only in ignored `.env`; the exhausted credential is retained locally without automatic fallback. The Agent Plan account is unchanged.

## Scope fixed before execution

Continue the [remaining 41 model/task pairs](ark-model-pending-2026-10-28.json): 366 new agent runs. Existing observations and missing-response records remain immutable. The earlier four full-coverage Pro/Lite groups are retained; no additional repetitions are added to them. The 11 earlier Pro recommendation replies remain separate observations and are not patched with selected replacement conditions.

Use the existing matrix entry point in two sequential batches, each with at most two concurrent groups:

1. All three tasks for the 13 models other than Doubao Seed 2.1 Pro/Lite: 39 complete groups, 338 conditions. This prioritizes model coverage.
2. Task003 for Doubao Seed 2.1 Pro and Lite: two new complete groups, 28 conditions.

If the first batch encounters an account availability block, do not launch the second batch. Preserve any unsupported-model, infrastructure, timeout or Judge errors without automatic repair or individual trial replacement. This is a new declared experiment, not resumption inside old groups. A fresh quota or rate block stops dispatch as specified in the runtime.

## Fixed configuration

- Tasks001 v0.8,002 v0.2,003 v0.1; materials, tools and rubrics unchanged.
- Local Codex ASP, existing generic model descriptors, medium requested effort, live native search, 300-second agent timeout and condition-order seed17.
- One run per condition; the larger quota does not change the repetition count.
- Same Coding Plan endpoint; account identity recorded as `coding-replacement-20261028`, without credentials in artifacts.
- Judge stays local4141, `gpt-6.1-sol`, medium. Each terminal complete group receives exactly one final-response-only call; no trajectories, materials or saved state are added.
- Both dated batches and the earlier batch are reported separately before any coverage summary. Changing account, time or model alias availability can introduce differences; cross-model choices alone do not establish OrgBias.

## Execution record

The continuation is authorized and declared. Actual progress is recorded in local `runs/` manifests and will be added here after execution. Previous reports describe the earlier stopped batch, not the current account's availability.
