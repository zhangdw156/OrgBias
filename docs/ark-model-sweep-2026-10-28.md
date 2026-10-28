# Ark named-model sweep, 2026-10-28

Status at protocol registration: implementation verified locally; one GLM-5.3 task003 condition completed as an engineering smoke. Full matrix results will be reported separately. No bias conclusion follows from that smoke.

## Registered experiment

- Tasks remain unchanged: 001 v0.8 (7 conditions), 002 v0.2 (5 conditions), 003 v0.1 (14 conditions).
- All 15 named text-generation models in the provider's October 28 documentation are candidates: Doubao Seed 2.1 Pro/Lite, Seed 2.0 Mini, Seed Evolving; MiniMax M3; Kimi K2.7 Code/K2.8 Preview/K3/K3.1 Pro; GLM 5.3/5.3 Flash; DeepSeek V4 Flash/V4 Pro/V4.1 Flash/V4.1 Flash Economy. Exact API IDs are pinned in `oribias/config/ark_models.json`.
- Auto routing is excluded because it is not one fixed model. Embedding and image/video/audio generation models do not implement these text-agent tasks. The two retiring text models are retained and runtime availability is reported.
- One run per condition: 45 task/model groups, 390 planned agent runs. This is exploratory; it cannot establish stable effects or equivalence. Seed 17 fixes each group's condition order; no repeated conditions are silently added.
- Same local Codex 0.157.1 ASP, generic prompt, task MCP tools and live native search setting. Each trial has isolated state. At most two groups execute concurrently on separate ASP ports. Medium reasoning is requested for all; this is not an equal-compute claim across providers.
- The rubric model is always `http://localhost:4141/v1`, `gpt-6.1-sol`, medium. Each terminal complete group receives one final-response-only call. Task materials, trajectories, saved state and summaries remain excluded. Invalid judge outputs are preserved without repair calls.
- No task, rubric, tool or offer changes are made to elicit a positive result. Analyze within-model organization sensitivity first. Differences in preferences between models alone are not OrgBias.

## Accounts and compatibility

The two credentials are stored only in ignored `.env`, under separate Coding Plan and Agent Plan prefixes. No credentials enter task containers or committed artifacts. Responses compatibility at `/api/coding/v3` was verified; retaining Codex avoids changing harness just to access the new models.

A minimal compatibility request to the Agent Plan account returned `AccountQuotaExceeded`, with weekly reset **2026-11-02 00:00:00 +0800**. That account is unavailable for this sweep. The Coding Plan account completed a compatibility request and the native Codex engineering smoke. The full matrix therefore selects the Coding Plan account explicitly; it does not switch accounts inside a group or turn quota failures into model findings.

The supplied Claude-specific `MAX_THINKING_TOKENS=0` is preserved locally but does not apply to Codex. The provider explicitly says GLM-5.3 and Kimi-K3 cannot disable thinking. Requested Codex effort is medium; actual provider interpretation may differ. The supplied 3,000,000 ms API timeout is also a Claude-specific preference; the actual per-trial wall-clock limit remains the existing 300 seconds.

Smoke group: `runs/20261028T120534Z-533000`, task003 rotation_01_forward, GLM-5.3. It read all offers and the report, saved P14 first and P28 backup, with no constraint violations. It is an engineering check during implementation, excluded from all matrix comparisons. Its catalogue was being refactored during the smoke, so it is not a frozen-provenance research sample.

## Failure policy and reporting

Keep every attempted trial and native error. An explicit quota/authentication failure stops pending requests to the affected account; an unsupported-model error blocks queued groups for that model. Already-running groups finish or preserve their own failure. Unstarted conditions are cancelled/blocked, not claimed as attempted or bias-free. There are no automatic trial/judge retries, substitutions or successful-only sample selection.

Each group records source hashes, task snapshot, model settings, effective catalogue, planned runs, complete final replies, exact task events, saved objective state and separate judge artifacts. The matrix manifest links all groups and logs. The GPT task003 reference used the same task v0.1; the older GPT hospital experiment used v0.1, so it is not a direct same-task comparison to this v0.2 sweep. Native search behavior and retrieved evidence may differ across providers.

## Sources

- [Coding Plan overview and named model list](https://www.volcengine.com/docs/82379/1925114), retrieved 2026-10-28.
- [Agent Plan overview and model list](https://www.volcengine.com/docs/82379/2366394), retrieved 2026-10-28.
- [Official OpenAI Codex advanced configuration](https://developers.openai.com/codex/config-advanced/), fetched to verify custom providers and Responses configuration.

Raw source captures and compatibility responses are retained under ignored `artifacts/ark-discovery/`. The general platform `/models` catalogue includes unrelated and shutdown entries and was not used as the list of included models.
