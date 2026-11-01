# Evidence, open questions and related work

Public-release assessment: November 1, 2026. This document summarizes existing experiments and literature comparisons. It does not report new inference or preregister new experiments.

## What the pilot evidence supports

The [public archive](../results/README.md) contains 101 final replies across 18 retained pilot groups, plus failed/cancelled conditions. Groups span different task versions, dates, accounts and settings. They are not a pooled estimate of bias prevalence. The 94 valid final-response classifications are all `no_observed_signal`; seven replies lack a valid Judge result. Positive labels in the separately marked authored controls are not experimental discoveries.

**Task001 v0.8:** the GPT reference and complete Doubao Pro/Lite groups each selected technical review for all seven organization conditions, preserving the claim date without payment. Wording differed but the principal recorded action was invariant in these groups. Earlier v0.6 and v0.7 are separate exploratory versions, not replications of v0.8.

**Task002 v0.2:** Doubao Pro/Lite always requested independent review. GLM-5.3 requested issuing-team follow-up for Mayo/undisclosed, independent review for Jishuitan/PUMCH, and clarification for Riverside. GLM Flash and Kimi chose other mixtures of clarification and independent review. These are observable decision differences. The management categories are not mutually exclusive beliefs: an agent can consider a supervised trial reasonable while deferring a decision until review. One sample per institution/model does not distinguish a stable identity effect from stochastic choices between reasonable routes. All actions are simulated; medical correctness and patient outcomes have not been established. The earlier GPT hospital data used v0.1 with a possible debiasing cue and are not a direct cross-model comparison to v0.2.

**Task003 v0.1:** the GPT reference selected P14 first and P28 as backup in all 14 brand/order conditions, including the anonymous controls. Doubao Pro selected P14 in all 11 available responses; one response selected P39 as backup on price grounds. The same brand assignment in the other presentation order selected P28. This does not isolate a manufacturer effect. The task fixes the candidate set, specifications and retailer assurances; it does not cover open-ended product discovery.

These pilots support limited stability observations and hypotheses about decisions worth repeating. They do not support declaring models unbiased, ranking companies by fairness, or claiming a reliable OrgBias detector. A source/identity effect and unjustified treatment are distinct questions.

## Measurement boundaries

- A single configured local Codex harness was used with different provider-reported model identifiers. Separate commercial personal-agent products and a model-by-harness factorial comparison have not been evaluated.
- Each organization/order condition usually has one sample. The one repeated GPT hospital group used an earlier task version. There are only three underlying cases.
- Live web search was allowed; external evidence was not held fixed. Exposed web requests are retained, but are not a complete retrieval log.
- The fixed local-provider `gpt-6.1-sol` medium Judge sees only prompts and final replies. It cannot validate unseen evidence or actual execution. Schema, identity and exact-quotation validation are integrity checks, not human validation of bias judgments.
- The public archive exposes trusted action state alongside final-text labels. A negative text label can coexist with action variation. A specialized evaluator and broad human calibration remain future work.
- The initial GPT v0.6 baseline recorded a dirty source tree. Its task snapshot and original source hashes are retained. Later clean batches are identified separately.
- Account failures, model rejections and failed Judge calls leave missing evidence. The October 29 batch ended on a Judge connection error after 15 successful agent runs; 38 groups/351 conditions never started. They are not negative observations. No failed Judge call was repaired for this release.

## Closest related work

The table describes research overlap, not a claim to exhaustive novelty review. Methods were checked in the cited versions. See the dated [four-paper review](four-paper-task-design-review-2026-10-27.md) and [personal-agent review](personal-agent-orgbias-review.md) for additional references and publication-status qualifications.

| Work | What it already studies | Boundary relevant to OrgBias |
|---|---|---|
| [Affiliation Bias in Peer Review of Abstracts by a Large Language Model](https://pmc.ncbi.nlm.nih.gov/articles/PMC10753437/) — JAMA | Fixed medical abstracts under different institution signatures; 30 abstracts × 31 conditions × 250 reviews; top–low acceptance difference about 1.7 percentage points | Hospital-name substitution follows an existing approach. Clinical advice and action auditing extend the setting, but do not alone establish a new mechanism. |
| [“Global is Good, Local is Bad?”](https://aclanthology.org/2024.emnlp-main.707/) — EMNLP 2024 | Associations between brands, global/local categories and product attributes | Primarily measures associations and choices; negative brand language is not automatically unfair treatment of a fixed case. |
| [DarkBench](https://openreview.net/forum?id=odjMSBSWRt) — ICLR 2025 | Dark patterns including preference for the chatbot's own company, model or products | Self-preference already has direct evaluation work; it differs from arbitrary organization substitution. |
| [A Scalable Entity-Based Framework for Auditing Bias in LLMs](https://arxiv.org/abs/2601.12374v3) | Fixed labeled templates with many entities, including companies; measures label-probability shifts | Entity effects need not change final decisions; publication status was not independently verified. |
| [Source Preference in the Wild](https://arxiv.org/abs/2610.03195v1) | Search agents across shopping, accommodation and scholarly requests; controlled source swaps; demand satisfaction, missing information and DPO interventions | “Agents prefer sources” and “fixed content, different source” are established research questions. Its source-swap experiment is a single-choice replay; its natural search workflow is multi-step. |
| [What Is Your AI Agent Buying?](https://arxiv.org/abs/2508.02630v3) | ACES shopping choices under randomized positions, prices, ratings and badges; model/version differences; seller description changes; screenshot and JSON interfaces | Cross-model choice differences and commercial cue effects are already studied. The workflow deliberately isolates selection and does not identify a pure company-name effect. The later [WWW 2026 proceedings record](https://doi.org/10.1145/3774904.3792943) is shorter; method details here refer to the December 15, 2025 long version. |
| [Ads in AI Chatbots?](https://arxiv.org/abs/2604.08525v3) | Explicit sponsorship instructions, expensive recommendations, unsolicited promotion, framing and disclosure under user/company conflicts | Measures commercial incentives introduced in the prompt; sponsor brands are randomized to reduce native brand effects. The paper and repository label it COLM 2026; that status is author-reported in our review. |
| [Magentic Marketplace](https://arxiv.org/abs/2510.25779v1) | Buyer and seller agents search, communicate, propose and simulate payments; first-proposal bias, search quality and manipulation | Multi-step agentic bias and user consequences already have direct precedents. Company-name substitution is not its main intervention. |

## Questions worth developing

1. **Verification and correction.** Does identity change whether an agent seeks evidence, and whether it revises its actions after receiving the same evidence? Compare voluntary acquisition with matched evidence exposure, controlling cost and access. Contract/fee scenarios may provide clearer ground truth than ambiguous clinical choices.
2. **Consequential actions.** Does a replicated identity effect alter claim preservation, avoidable charges, scheduling, resource use or errors? Measure outcomes directly where possible; neither action variation nor task failure alone establishes bias.
3. **Preference attribution and memory.** Does an agent mistake its own organization choice for an expressed user preference, store it, and reuse it? Distinguish user statements, agent inferences and actual experience. [Memory-Induced Tool-Drift](https://arxiv.org/abs/2605.24941) already studies biased memories affecting tools; “memory plus bias” is not by itself a new contribution.
4. **Measurement quality.** How well do categorical judges detect supported asymmetries versus ordinary uncertainty or reasonable alternatives? Use independent human annotations, credible positive/negative controls and untouched cases; retain disagreements.

These are candidate research questions, not proven gaps or positive findings. Merely adding domains, tools, models or a trained judge is not an automatic novelty claim. A carefully designed benchmark or replication can still be valuable if it resolves a clear empirical uncertainty. We welcome work that strengthens, revises or contradicts our current interpretation.
