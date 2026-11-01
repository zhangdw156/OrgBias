# Public release preparation — November 1, 2026

OrgBias is being shared as an open research starting point. The release invites independent replications, corrections, stronger tasks, calibrated evaluations and useful positive or negative results. It does not claim a validated benchmark, a completed 15-model sweep, or established organizational bias.

## Released evidence

The fixed export allowlist contains 18 retained pilot groups with 138 conditions: 101 final replies, 33 failed conditions and four cancellations. Ninety-four replies have valid no_observed_signal classifications; seven replies have unavailable Judge results. Thirteen additional group records are explicitly marked as engineering exclusions or authored evaluator controls. Seven matrix/continuation manifests preserve unstarted jobs without treating overlapping plans as independent coverage.

The public views include full final replies, rendered prompts, observed task-tool calls and returns, saved task state/outcomes, visible web requests, task snapshots and original Judge inputs/results. All exported final reply strings match their original recorded strings. Failed Judge artifacts remain failed. No inference request, failed condition or Judge was rerun for publication.

Native provider/harness wrappers, hidden reasoning, browser caches, downloaded papers and retrieved third-party page bodies remain excluded. The task fixtures are synthetic; the private/ directories describe simulator visibility, not personal data. Local filesystem paths and provider request IDs are removed from the public views. Original source/artifact hashes and exported-file hashes are recorded separately in results/provenance.json and results/checksums.json.

## Local verification

- Checked 307 unique blobs reachable from the existing Git history for known local credentials and common credential/private-key patterns; no matches were found. Commit history is retained for experimental source provenance, including historical author metadata and dated documentation.
- Checked current tracked material and new public evidence against local credential values. No matches or email addresses in the exported evidence were found.
- Verified 1,207 release files, 31 group inventories and 18 saved Judge outputs. Checks cover hashes, schemas, identities, exact quotations and consistency between saved outcomes and trusted snapshots. They do not validate substantive bias labels or medical correctness.
- Ran all 43 existing local software tests successfully. These include local transport and simulated scheduling checks, not new model inference.
- Checked the curated README, contribution guide, document navigation and all public group indexes for broken local links; none were found. Historical task snapshots retain their original documentation and are not used as release navigation.
- Verified the public evidence again from a temporary checkout containing only staged files, without .env, runs/ or artifacts/, using the existing project Python dependencies. This confirms the archive has no dependency on private runtime files; it is not a separate clean dependency installation.
- Kept task instructions, workspace fixtures, service behavior, rubric logic, runtime model settings and uv dependency versions unchanged. No credentials are needed to browse or verify the release.

Original contributions use Apache-2.0; Codex attribution is retained in NOTICE and oribias/config/. Model-generated records and linked third-party material are not represented as exclusively owned by this project. The public README and CONTRIBUTING.md explain reuse, citation and evidence standards.

This preparation record describes local checks. Publication and remote CI status can be verified through the repository history and Actions page; local passing tests are not a claim about an unobserved remote run.
