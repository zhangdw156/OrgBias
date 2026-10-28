# Research and design documents

Updated: 2026-10-28. The benchmark is English throughout, and all materials for the first task live in [tasks/001](../tasks/001/README.md). Project-level research and engineering notes remain here. Independent ASP deployment is mandatory. The first local implementation uses a host Codex ASP, Harbor, a task-only Docker image, and one final-response judge call. See the runtime guide for execution and validation scope.

| Document | Contents | Status |
|---|---|---|
| [Ark continuation](ark-model-continuation-2026-10-28.md) | Replacement account; 41 remaining pairs in newly declared complete groups | Registered; one run per condition, fixed GPT Judge |
| [Ark partial results](ark-model-results-2026-10-28.md) | Exact coverage, cross-model observations, errors, traces and remaining work | 35 replies: no_observed_signal; 24 HTTP429 failures; 331 conditions unstarted |
| [Ark named-model sweep](ark-model-sweep-2026-10-28.md) | 15 named text models × 3 current tasks, independent fixed GPT judge, quota and failure policy | Registered protocol and explicit engineering amendments |
| [Laptop recommendation task](../tasks/003/README.md) | Six fixed profiles, brand rotation, order controls, persisted choices and categorical evaluation | English v0.1; see task-local validation |
| [Task 003 first complete group](../tasks/003/results/2026-10-28-first-group.md) | All 14 outcomes, one group Judge, invariant recommendations and interpretation limits | 14 completed; 14 no_observed_signal |
| [Task 003 browser research](../tasks/003/research.md) | Nine source pages, measurement/contract distinctions and synthetic-fixture provenance | Browser capture records retained locally |
| [Four-paper task-design review](four-paper-task-design-review-2026-10-27.md) | Original task construction, author-code checks, diagnosis of our tasks, and interpretable null results | Research review; proposed designs not yet run |
| [Local runtime](local-runtime.md) | Configuration, actual commands, architecture, outputs, and limits | Local Codex ASP implementation |
| [2026-10-27 local debug](local-debug-2026-10-27.md) | Seven real Codex runs, one judge call, earlier failures, and validation boundaries | Debug group completed; not the 35-run pilot |
| [Bounded iteration report](bounded-iteration-report-2026-10-27.md) | Task variants, actual findings, hospital extension and limitations | Updated through delivery |
| [Result extract](iteration-results-2026-10-27.json) | Per-response categories, trusted outcomes and artifact hashes | Complete judged groups only |
| [Bounded iteration plan](task001-iteration-plan-2026-10-27.md) | Deadline, fixed conditions, selection and repetition rules | Recorded before dependent runs |
| [Iteration ledger](task001-iteration-ledger.json) | Every tested version and group identifier | Includes negative results |
| [Research plan](research-plan.md) | Scope, accepted decisions, and evaluation principles | Current project guidance |
| [Task 001 specification](../tasks/001/README.md) | Case, package layout, and one-call classification of each final response | English v0.8; local runtime implemented |
| [Hospital affiliation task](../tasks/002/README.md) | Identical clinical opinion under five institution identities; care memo and next-step actions | v0.1: ten GPT replies; v0.2: ten Pro/Lite replies, all no_observed_signal |
| [Task instruction](../tasks/001/instruction.md) | English user query, manufacturer placeholder, and unattended authorization | English instruction; used by local debugging |
| [Response rubric](../tasks/001/rubric.md) | Cross-organization comparison using final replies, with one result per response | English v0.7 rubric retained; synthetic controls checked |
| [Judge input template](../tasks/001/judge_input.md) | Task prompts and all final-response records for one LLM call | English template; API client implemented |
| [Material contract](../tasks/001/contract.md) | Visibility, rendering, service rules, and single-call judge input | English v0.8; runtime implemented |
| [Initial workspace](../tasks/001/workspace/) | Four text documents for voluntary agent reading | Templates available |
| [Private inspection report](../tasks/001/private/inspection_report.txt) | Report returned only by the case service | Fixture available; not an initial agent input |
| [Organization conditions](../tasks/001/organizations.json) | English brand values and the undisclosed control | Configuration and runner available |
| [Engineering design](engineering-design.md) | ASP boundary, Harbor interfaces, environment isolation, and final-response aggregation | Current local implementation |
| [Agent/task deployment review](agent-task-deployment-review.md) | Independent ASP deployment and official project comparisons | Source review only |
| [Laptop scenario research](laptop-orgbias-pilot-research.md) | Brand-related source material, candidate cases, and evidence limits | Research record |
| [Personal-agent literature review](personal-agent-orgbias-review.md) | Source preference, shopping agents, and user-interest studies | Publication status is qualified within the review |

Read the research plan and task specification before using the task. The judge is fixed to one LLM call per complete group, using only task prompts and final responses as evidence and returning one result per response. Trajectories and authoritative outcomes remain separate. The API client and JSON schema validation are implemented; obvious synthetic evaluator controls have been checked, while human calibration and subtle-signal sensitivity remain unresolved.

Keep links and current instructions synchronized when decisions change. Do not revive numerical bias scores, independent per-run bias judgments, or task-local agent installation. Historical research notes retain their original source dates and verification limits. Raw captures, private source material, and runtime artifacts are not task inputs.
