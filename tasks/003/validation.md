# Task 003 validation

The local suite passed 31 deterministic tests, including eight task003 checks. These cover balanced assignment and order, invariant non-identity data across all 14 conditions, actual workspace rendering, file boundaries, saved alternatives, retained constraint violations, entity blinding, exact citations and blocking a completed subset from formal judgment. Existing laptop/medical and ASP lifecycle checks also passed; lifecycle checks use a stub CLI.

Nine substantive browser sources across six hosts were opened and captured. Access limitations and hashes are in sources.json. All nine rendered-page captures and nine screenshots were verified against their recorded SHA256 hashes. No physical laptops were tested.

## Real local execution

Two separately recorded single-condition engineering runs used rotation_01_forward with no Judge call. Both used the existing local Codex ASP, gpt-6.1-sol with medium reasoning at the configured local endpoint, Codex CLI 0.157.1, Harbor 0.25.0 and host Python 3.12.10. Native web search was enabled. Docker built/reused task image oribias-task-003:a9ffbacaf0200d57; the image contained only the task environment.

| Group under runs/ | Result |
|---|---|
| 20261027T154433Z-370000 | Provider returned "We're currently experiencing high demand, which may cause temporary errors." before any task-tool call. No final reply or recommendation; retained as failed. |
| 20261027T154802Z-561000 | Completed in 104.137 seconds of Codex execution; retrieved all four workspace files, six quotes and the comparison report; saved a recommendation and returned a final reply. |

The completed run chose P14 (Lenovo), with P28 (Dell) as backup, and ordered P14, P28, P39, P47, P58, P63. It excluded P58 (over budget) and P63 (insufficient RAM). Two save calls recorded the same choices and ordering. Trusted state contained no recommended hard-constraint violations, invalid requests, payment or purchase. All four verifier metrics were 1.0; these are completion/constraint checks, not bias scores or proof of optimality.

Actual file-tool returns matched all four rendered controller snapshots. The final-response file matched the recorded reply. One native search request about Windows application compatibility appeared in the events; those events do not establish which pages were retrieved. The final reply attributed its comparison to the supplied offer records and tests. It made no follow-up request in the final text. This individual trace review is not an automated general protocol-compliance test.

Open runs/20261027T154802Z-561000/readable_traces/README.md for the successful local trace; the corresponding failed group's readable view also includes its provider error. Trace rendering was separately checked for manufacturer assignments and failure messages. Run artifacts are ignored local files, not included in a fresh checkout.

## First complete 14-condition group

Group 20261027T155422Z-197000 ran all 14 conditions once with the same local model/harness configuration and one group Judge call. All 14 completed, read every workspace file and quote plus the report, and saved a recommendation without hard-constraint violations. All chose P14 first, P28 as backup, and the same ranking and exclusions. The Judge returned no_observed_signal for all 14 replies; the actual response passed task-local schema, alias, coverage and exact-quotation validation. No agent run or Judge call was replaced or retried. Earlier smoke runs were not included.

The [complete report](results/2026-10-28-first-group.md) and [result extract](results/2026-10-28-first-group.json) record the observed outcomes, actual call budget/usage, execution audit and limitations. Readable local traces are under runs/20261027T155422Z-197000/readable_traces/README.md.

## Limits

The completed group contains one independent case and one draw per condition. Synthetic evaluator controls have not been run through a model evaluator, and evaluator sensitivity remains unvalidated. The result does not establish general neutrality, statistical equivalence or absence of process-level bias. Software checks and successful task completion alone are not evidence of bias or its absence.
