"""Check all reachable Git history without printing matched private values.

Uses only the standard library and Git. This is a regression guard for common
credentials and personal metadata, not a guarantee that every secret is found.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
EMAIL = re.compile(rb"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")
PATTERNS = {
    "credential": re.compile(
        rb"(?<![A-Za-z0-9_-])(?:ark-[a-f0-9]{8}-[a-f0-9-]{25,}"
        rb"|sk-(?:proj-|ant-)?[A-Za-z0-9_-]{25,}"
        rb"|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}"
        rb"|(?:AKIA|ASIA)[A-Z0-9]{16}|xox[baprs]-[A-Za-z0-9-]{20,}"
        rb"|-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----)"
    ),
    "personal_path": re.compile(
        rb"(?:/Users/|/home/)[A-Za-z0-9_.-]+/"
        rb"|(?:/private)?/var/folders/[A-Za-z0-9]{2}/[A-Za-z0-9_-]{6,}/"
    ),
    "provider_request_id": re.compile(
        rb'(?i)(?:request[_ -]?id[:=]\s*)[A-Za-z0-9_-]{16,}'
        rb'|"request_id"\s*:\s*"[A-Za-z0-9_-]{16,}"'
    ),
}


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], stderr=subprocess.PIPE)


def public_emails(repo):
    """Explicit publication choices, separate from credential checks."""
    name = ".privacy-public-emails"
    if not git(repo, "ls-tree", "--name-only", "HEAD", "--", name).strip():
        return set()
    addresses = set()
    for line in git(repo, "show", f"HEAD:{name}").splitlines():
        line = line.strip()
        if not line or line.startswith(b"#"):
            continue
        if EMAIL.fullmatch(line) is None:
            raise ValueError("Malformed address in the public contact list")
        addresses.add(line.lower())
    return addresses


def safe_email(match, published):
    address = match.group().lower()
    domain = match.group(1).lower()
    return (address in published
            or domain in {b"users.noreply.github.com", b"example.com", b"example.org", b"example.net"}
            or domain.endswith((b".test", b".invalid"))
            or address in {b"git@github.com", b"git@gitlab.com"})


def local_credentials(repo):
    """Optional comparison against ignored local values; never emit the values."""
    path = repo / ".env"
    values = []
    if path.is_file():
        for line in path.read_text().splitlines():
            if line.lstrip().startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            value = value.strip().strip("\"'")
            if (re.search(r"KEY|TOKEN|SECRET|PASSWORD", key, re.I) and len(value) >= 12
                    and not value.startswith(("replace-", "${"))):
                values.append(value.encode())
    return values


def audit(repo):
    repo = Path(repo).resolve()
    if git(repo, "rev-parse", "--is-shallow-repository").strip() != b"false":
        raise ValueError("Full history is required; a shallow checkout cannot pass this audit")
    objects = git(repo, "rev-list", "--objects", "--all").decode().splitlines()
    values = local_credentials(repo)
    published = public_emails(repo)
    counts, findings = Counter(), []
    process = subprocess.Popen(["git", "-C", str(repo), "cat-file", "--batch"],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def add(kind, oid, path, data=b"", offset=0):
        findings.append({"kind": kind, "object": oid, "file": path or "(Git metadata)",
                         "line": data[:offset].count(b"\n") + 1})

    try:
        for entry in objects:
            oid, _, path = entry.partition(" ")
            process.stdin.write((oid + "\n").encode())
            process.stdin.flush()
            header = process.stdout.readline().split()
            if len(header) != 3:
                raise ValueError("Cannot read a reachable Git object")
            data = process.stdout.read(int(header[2]))
            if process.stdout.read(1) != b"\n":
                raise ValueError("Incomplete Git object read")
            kind = header[1].decode()
            counts[kind] += 1
            if kind not in {"blob", "commit", "tag"}:
                continue
            name = Path(path).name
            if (name == ".env" or (name.startswith(".env.") and name != ".env.example")
                    or name in {"auth.json", "credentials.json", "id_rsa", "id_ed25519"}):
                add("private_file", oid, path)
            for label, pattern in PATTERNS.items():
                for match in pattern.finditer(data):
                    add(label, oid, path, data, match.start())
            for match in EMAIL.finditer(data):
                if not safe_email(match, published):
                    add("unreviewed_email", oid, path, data, match.start())
            for value in values:
                if value in data:
                    add("known_local_credential", oid, path, data, data.index(value))
    finally:
        process.stdin.close()
        process.stdout.close()
        process.wait()
    if process.returncode:
        raise ValueError("Git object scan did not finish successfully")
    return {"objects": dict(counts), "local_credentials_compared": len(values),
            "finding_counts": dict(Counter(row["kind"] for row in findings)),
            "findings": findings}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        report = audit(args.repo)
    except (ValueError, subprocess.CalledProcessError) as exc:
        # Git errors may contain local paths; do not echo their raw output.
        print(json.dumps({"error": str(exc) if isinstance(exc, ValueError) else "Git scan failed"}))
        return 2
    print(json.dumps(report, indent=2))
    return 1 if report["findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
