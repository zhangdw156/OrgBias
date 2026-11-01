# Git history audit — November 1, 2026

The owner explicitly chooses to publish `zhangdawei24@mails.ucas.ac.cn` as a contributor contact. This is intentional public attribution, not a privacy incident. The earlier decision to hide that address and describe its cached history as a leak was incorrect. Future commits again use the chosen public address, and no GitHub Support request is needed for this email. The unsent email-removal draft has been withdrawn.

## Scope and findings

- Inspected all advertised remote refs: one main branch, no tags or pull-request refs.
- Scanned all 25 original commits and 956 unique reachable blobs, including deleted and superseded contents, commit metadata and messages.
- Compared against four local credential values without printing them. Gitleaks 8.30.1 also scanned the complete history with redacted output. Neither check found a real credential or private key.
- Reviewed host paths, emails, private-network addresses, phone-number candidates and provider request identifiers. The phone-number candidate was a public complaint URL identifier. A broad token-prefix candidate was a documentation link, not a key.
- Actual `.env`, raw runs and runtime artifacts had never been tracked. Clinical and customer fixtures are synthetic.

## Changes and provenance

Historical repository paths were made relative and provider request identifiers were redacted. These changes remain. The original history was backed up outside the repository in a local directory restricted to its owner.

The earlier rewrite also replaced the owner's email before their publication preference was clarified. Those existing commits are retained to avoid another history rewrite; new commits use the owner's public address. Every rewritten revision was compared with its original: task definitions, runtime source, fixtures, rubrics and the public experiment archive were unchanged. No model calls were made.

Rewriting metadata changed commit IDs. Original `git_commit` and `source_commit` fields in experimental records remain as recorded. Use the [commit mapping](history-commit-map.json) to find the corresponding current revision, and each public group's task snapshot to inspect its saved materials.

## Ongoing checks

Run the full-history check without model access or third-party Python dependencies:

```bash
python scripts/audit_git_privacy.py
```

The check covers all reachable refs and refuses shallow checkouts. Credentials, local paths and private configuration are checked independently of public contact addresses. Addresses intentionally published with their owners' consent are recorded in [.privacy-public-emails](../.privacy-public-emails); a GitHub no-reply address is optional. An unlisted email match requires review of its intended visibility, not an automatic conclusion that it was leaked.

The check reports object IDs, filenames and line numbers without echoing unreviewed values. The GitHub verification workflow fetches full history first. Regression tests cover historical credentials, metadata on unmerged branches, explicit public contacts, unrelated email matches, safe examples and ignored local credentials.

The earlier cleanup passed 46 local software tests, the unchanged 1,207-file public-evidence verification, and GitHub CI. These were software and archive checks, not model inference. The contact-policy correction adds a regression test; its result is recorded in CI.

Pattern checks cannot establish that every possible secret is absent. GitHub may retain old objects after a history rewrite; the owner's voluntarily published email in such objects is not an unresolved privacy issue. No support request has been sent.
