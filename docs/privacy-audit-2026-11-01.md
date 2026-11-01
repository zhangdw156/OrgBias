# Git history privacy audit — November 1, 2026

The initial release's credential scan did not cover personal commit metadata adequately. A follow-up audit found a personal email address in the author and committer fields of all 25 commits, host-specific paths in nine historical document paths, and provider request identifiers in older reports. These were privacy issues even though the current exported evidence had already been sanitized.

## Scope and findings

- Inspected all advertised remote refs: one main branch, no tags or pull-request refs.
- Scanned all 25 original commits and 956 unique reachable blobs, including deleted and superseded file contents, commit metadata and messages.
- Compared against four local credential values without printing them. Gitleaks 8.30.1 also scanned the complete history, with redacted output. Neither check found a real credential or private key.
- Reviewed personal paths, emails, private-network addresses, phone-number candidates and provider request identifiers. The phone-number candidate was a public complaint URL identifier. A broad token-prefix candidate was a documentation link, not a key.
- Actual `.env`, raw runs and runtime artifacts had never been tracked. The clinical and customer fixtures are synthetic.

## Cleanup and provenance

The original history was backed up outside the repository in a local directory restricted to its owner. All 25 commits were preserved, replacing personal author/committer email fields with the owner's GitHub no-reply address. Historical repository paths were made relative, and provider request identifiers were redacted. The project-local Git email setting now uses the same no-reply address; global Git settings were not changed.

Every rewritten revision was compared with its original. Only historical documentation blobs and commit metadata changed. Runtime source, tasks, fixtures, rubrics and the public experiment archive were unchanged; the tree at the publication commit was identical before and after the rewrite. No model calls were made. This follow-up adds documentation, an offline privacy check and its regression tests.

Rewriting metadata changes commit IDs. Original `git_commit` and `source_commit` fields in experimental records remain unmodified identifiers of what was recorded. Use the [commit mapping](history-commit-map.json) to find the corresponding sanitized revision, and each public group's task snapshot to inspect its saved task materials. No old-history branch or tag is retained on the public remote.

## Ongoing checks and limits

The full-history regression check is available without model access or third-party Python dependencies:

```bash
python scripts/audit_git_privacy.py
```

It checks all reachable refs and refuses shallow checkouts. It reports object IDs, filenames and line numbers without echoing private values. The GitHub verification workflow fetches full history before running it. Three local regression tests cover deleted credentials, metadata on an unmerged branch, redacted output, safe examples and comparison with ignored local credentials.

After cleanup, all 46 local software tests and the unchanged 1,207-file public-evidence verification passed. These were offline/local simulated checks using the existing project environment, not new model inference or a separate dependency installation. Gitleaks and the history regression check found no remaining matches in the sanitized history.

Pattern checks cannot prove that every possible secret or personal detail is absent. A history rewrite removes the old commits from the advertised branch history; it does not erase existing clones, downloads, or GitHub's cached/unreferenced objects. Those require separate verification and, when retained by GitHub, a GitHub Support cleanup. Do not merge pre-cleanup history back into the public branch.
