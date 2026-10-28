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

The first replacement-account attempt, `runs/matrix-20261028T142551Z-673000`, stopped on native HTTP429. It attempted ten Mini conditions: two final replies, six explicit unsupported-model HTTP404 failures and two HTTP429 failures. Two more conditions in the started groups were cancelled; all 37 queued groups were blocked. The subsequent Pro/Lite recommendation batch was not launched. Both group Judge calls returned HTTP401 with an upstream organization-access error; neither produced a valid classification. Raw failures, the two replies and states are retained in the [attempt extract](ark-model-replacement-attempt-2026-10-28.json).

The first unsupported-model messages omitted the structured `UnsupportedModel` code, so detection did not initially stop dispatch within the active groups. Manual evidence markers were subsequently superseded by the native HTTP429 blocks. The controller now recognizes that explicit provider rejection text as well; five focused settings/detection tests passed. Final replies merely discussing the error do not trigger this block. A rejection records availability at that time, not permanent model incapability.

Small follow-up diagnostic requests succeeded for both GLM-5.3 and Mini, and the unchanged GPT Judge succeeded on both a plain request and a structured-output request. These are connection diagnostics, not benchmark trials or repairs of failed Judge calls. They do not identify the earlier HTTP429's specific limit or establish reliable availability. No new-account weekly-exhaustion claim is supported.

## Serial continuation amendment

After those successful diagnostics, declare a new continuation with **one concurrent group**. Keep the two completed Mini replies and both failed Judge calls separate; no individual trial or Judge call is retried in place. All 41 pending pairs still require complete coverage. Run the other 12 models on all three tasks first (312 conditions), then Pro/Lite task003 (28), then fresh full Mini groups on all three tasks (26), for 366 declared conditions. Record the new source commit and execution time separately. The task content, model settings and one-call evaluation rule remain unchanged. If account-level HTTP429 recurs, stop this continuation rather than repeatedly restarting it. Actual matrices are linked in local `runs/continuation-*/manifest.json`.
