# Research and design documents

Updated: 2026-10-27. The benchmark is English throughout, and all materials for the first task live in [tasks/001](../tasks/001/README.md). Project-level research and engineering notes remain here. Independent ASP deployment is mandatory. The task environment and model experiments have not been implemented or run.

| Document | Contents | Status |
|---|---|---|
| [Research plan](research-plan.md) | Scope, accepted decisions, and evaluation principles | Current project guidance |
| [Task 001 specification](../tasks/001/README.md) | Case, package layout, and one-call classification of each final response | English v0.5; runtime pending |
| [Task instruction](../tasks/001/instruction.md) | English user query, manufacturer placeholder, and unattended authorization | English v0.4; not evaluated |
| [Response rubric](../tasks/001/rubric.md) | Cross-organization comparison using final replies, with one result per response | English v0.5; calibration pending |
| [Judge input template](../tasks/001/judge_input.md) | Task prompts and all final-response records for one LLM call | English template available; API call pending |
| [Material contract](../tasks/001/contract.md) | Visibility, rendering, service rules, and single-call judge input | English v0.5; implementation pending |
| [Initial workspace](../tasks/001/workspace/) | Four text documents for voluntary agent reading | Templates available |
| [Private inspection report](../tasks/001/private/inspection_report.txt) | Report returned only by the case service | Fixture available; not an initial agent input |
| [Organization conditions](../tasks/001/organizations.json) | English brand values and the undisclosed control | Configuration available; runner pending |
| [Engineering design](engineering-design.md) | ASP boundary, Harbor interfaces, environment isolation, and final-response aggregation | v0.5 design; not implemented |
| [Agent/task deployment review](agent-task-deployment-review.md) | Independent ASP deployment and official project comparisons | Source review only |
| [Laptop scenario research](laptop-orgbias-pilot-research.md) | Brand-related source material, candidate cases, and evidence limits | Research record |
| [Personal-agent literature review](personal-agent-orgbias-review.md) | Source preference, shopping agents, and user-interest studies | Publication status is qualified within the review |

Read the research plan and task specification before using the task. The judge is fixed to one LLM call per complete group, using only task prompts and final responses as evidence and returning one result per response. Trajectories and authoritative outcomes remain separate. The API client and final machine-readable output serialization are not implemented.

Keep links and current instructions synchronized when decisions change. Do not revive numerical bias scores, independent per-run bias judgments, or task-local agent installation. Historical research notes retain their original source dates and verification limits. Raw captures, private source material, and runtime artifacts are not task inputs.
