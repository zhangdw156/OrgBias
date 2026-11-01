"""Export existing local experiments; never execute agents or call a model.

The allowlist separates pilot observations from engineering runs and authored
evaluator controls. Source files remain untouched. Run from any working directory
with the project's Python: uv run python scripts/export_results.py.
"""
from collections import Counter
from hashlib import sha256
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "results"
PILOTS = {
    "20261027T115111Z-349000": "GPT screen v0.6 baseline; source working tree was dirty",
    "20261027T125411Z-678000": "GPT screen v0.7 exploratory revision",
    "20261027T131002Z-073000": "GPT screen v0.8 exploratory revision",
    "20261027T132541Z-133000": "GPT hospital v0.1; material contains a possible debiasing cue",
    "20261027T155422Z-197000": "GPT recommendation v0.1",
    "20261028T122426Z-188000": "Corrected Ark sweep",
    "20261028T122426Z-419000": "Corrected Ark sweep",
    "20261028T123510Z-181000": "Corrected Ark sweep; incomplete replies",
    "20261028T123811Z-491000": "Corrected Ark sweep",
    "20261028T124815Z-928000": "Corrected Ark sweep",
    "20261028T125706Z-009000": "Corrected Ark sweep; no replies",
    "20261028T125922Z-352000": "Corrected Ark sweep; no replies",
    "20261028T142551Z-118000": "Replacement-account attempt; no valid Judge result",
    "20261028T142551Z-756000": "Replacement-account attempt; no valid Judge result",
    "20261028T143438Z-553000": "Serial continuation; incomplete replies",
    "20261029T030034Z-560000": "Paced hospital sweep",
    "20261029T030607Z-970000": "Paced hospital sweep",
    "20261029T031703Z-358000": "Paced hospital sweep; complete replies, Judge HTTP500",
}
COLLISION = {
    "20261028T120848Z-450000", "20261028T120848Z-815000",
    "20261028T121836Z-643000", "20261028T122210Z-659000",
}
# All other groups in the fixed release are engineering-only or synthetic controls.
EXTRAS = COLLISION | {
    "20261027-evaluator-controls-task002-v01", "20261027-evaluator-controls-v07",
    "20261027T114555Z-301000", "20261027T114802Z-788000",
    "20261027T114928Z-101000", "20261027T124647Z-703000",
    "20261027T154433Z-370000", "20261027T154802Z-561000",
    "20261028T120534Z-533000",
}
MATRICES = [
    "matrix-20261028T120847Z-164000", "matrix-20261028T122426Z-836000",
    "matrix-20261028T142551Z-673000", "matrix-20261028T143438Z-168000",
    "matrix-20261029T030034Z-406000",
    "continuation-20261028T142551Z", "continuation-serial-20261028T143438Z",
]
SECRET = re.compile(r"(?:ark-[a-f0-9]{8}-[a-f0-9-]{25,}|sk-(?:proj-|ant-)?[A-Za-z0-9_-]{25,}|gh[pousr]_[A-Za-z0-9]{30,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----)")
LOCAL = re.compile(r"(?:/private)?/var/folders/[^\s\"'`<>]+|/Users/[^/\s]+/[^\s\"'`<>]+")
REQUEST_ID = re.compile(r"(?i)(request[_ -]?id[:=]\s*)[A-Za-z0-9_-]{16,}")
AUDIT = {}


def digest(data):
    return sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_text())


def clean(text):
    # Local paths and request identifiers have no scientific role in these data.
    text = text.replace(str(ROOT) + "/", "")
    text = LOCAL.sub("[local-path]", text)
    text = REQUEST_ID.sub(r"\1[redacted]", text)
    text = re.sub(r'("request_id"\s*:\s*)"[^"\n]+"', r'\1"[redacted]"', text)
    if SECRET.search(text):
        raise ValueError("Potential credential in export; inspect locally before publishing")
    return text


def write(path, text, source=None):
    public = clean(text)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(public)
    if source is not None:
        original = source.read_bytes()
        AUDIT[str(path.relative_to(DEST))] = {
            "source": str(source.relative_to(ROOT)),
            "original_sha256": digest(original),
            "public_sha256": digest(path.read_bytes()),
            "transformed": original != path.read_bytes(),
        }


def write_json(path, value, source=None):
    write(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n", source)


def copy_text(source, dest):
    write(dest, source.read_text(), source)


def fence(value):
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2)
    marker = "`" * max(3, max((len(x) + 1 for x in re.findall(r"`+", text)), default=3))
    return f"{marker}\n{text}\n{marker}"


def export_group(gid):
    source = ROOT / "runs" / gid
    target = DEST / "groups" / gid
    manifest = load(source / "manifest.json")
    cohort = "pilot" if gid in PILOTS else "authored_control" if "evaluator-controls" in gid else "engineering_excluded"
    reason = PILOTS.get(gid) or (
        "Authored evaluator examples, not observed agent responses" if cohort == "authored_control"
        else "Entire batch excluded after container namespace collision; labels are not research findings" if gid in COLLISION
        else "Single-condition engineering smoke; not a complete research group"
    )
    copy_text(source / "manifest.json", target / "manifest.json")
    for name in ["outcomes.json", "judge_response_ids.json", "provider_block.json"]:
        if (source / name).is_file():
            copy_text(source / name, target / name)
    for p in sorted((source / "task_source").rglob("*")):
        if p.is_file() and (p.suffix in {".md", ".json", ".txt", ".toml", ".py", ".sh"} or p.name == "Dockerfile"):
            copy_text(p, target / "task" / p.relative_to(source / "task_source"))
    for name in ["input.json", "request.json", "result.json", "budget.json", "implementation.json", "call_started.json", "http_status.json", "error.txt"]:
        if (source / "judge" / name).is_file():
            copy_text(source / "judge" / name, target / "judge" / name)
    # Failed response bodies are useful evidence; successful raw wrappers can contain
    # provider metadata and are redundant with the validated result.
    if not (source / "judge/result.json").exists() and (source / "judge/raw_response.txt").exists():
        copy_text(source / "judge/raw_response.txt", target / "judge/raw_response.txt")
    judged = load(source / "judge/result.json") if (source / "judge/result.json").exists() else None
    mapping = load(source / "judge_response_ids.json") if (source / "judge_response_ids.json").exists() else {}
    labels = {mapping.get(row["response_id"], row["response_id"]): row for row in (judged or {}).get("results", [])}
    outcomes = {r["response_id"]: r for r in load(source / "outcomes.json")} if (source / "outcomes.json").exists() else {}
    organizations = {o["org_id"]: o for o in manifest["organizations"]}
    rows = []
    for plan in manifest["planned_runs"]:
        rid = plan["response_id"]
        record_file = source / "records" / f"{rid}.json"
        record = load(record_file) if record_file.exists() else None
        final = record.get("final_response") if record else None
        status = record["run_status"] if record else "record_missing"
        agent = source / "harbor" / plan.get("harbor_trial_name", rid) / "agent"
        if not agent.exists():
            agent = source / "harbor" / rid / "agent"
        prompt_file = source / "prepared" / plan["org_id"] / "instruction.md"
        snapshot_file = agent / "case_snapshot.json"
        snapshot = load(snapshot_file) if snapshot_file.exists() else None
        objective = outcomes.get(rid, {}).get("objective")
        if snapshot is not None and objective is not None:
            if snapshot["objective"] != objective:
                raise ValueError(f"Snapshot/outcome mismatch: {gid}/{rid}")
        final_file = agent / "final_response.txt"
        if final is not None and final_file.exists() and final_file.read_text().strip() != final.strip():
            raise ValueError(f"Final file/record mismatch: {gid}/{rid}")
        web, errors = [], []
        events_file = agent / "events.jsonl"
        if events_file.exists():
            for line in events_file.read_text().splitlines():
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    # A truncated event stream remains recorded as an audit limitation.
                    errors.append("Unparseable native event line; omitted from this derived view")
                    continue
                item = event.get("item", {})
                if event.get("type") == "item.completed" and item.get("type") == "web_search":
                    web.append(item.get("action") or {"query": item.get("query")})
                if event.get("type") in {"error", "turn.failed"} or item.get("type") == "error":
                    message = item.get("message") or event.get("message") or event.get("error", {}).get("message")
                    if message and message not in errors:
                        errors.append(message)
        original_hashes = {name: digest(p.read_bytes()) for name, p in {
            "record": record_file, "prompt": prompt_file, "case_snapshot": snapshot_file,
            "native_events": events_file, "final_file": final_file,
        }.items() if p.is_file()}
        judge_row = labels.get(rid)
        response = {
            "response_id": rid, "org_id": plan["org_id"], "repetition": plan["repetition"],
            "cohort": cohort, "run_status": status, "record_present": record is not None,
            "record": record, "prompt": prompt_file.read_text() if prompt_file.exists() else None,
            "organization": organizations[plan["org_id"]], "objective": objective,
            "case_snapshot": snapshot, "web_requests": web, "runtime_errors": errors,
            "judge": judge_row,
            "judge_status": judge_row["status"] if judge_row else "unavailable",
            "original_artifacts_sha256": original_hashes,
            "original_final_response_sha256": digest(final.encode()) if final is not None else None,
            "public_final_response_sha256": digest(clean(final).encode()) if final is not None else None,
        }
        timing = agent / "provider_requests.json"
        if timing.exists():
            response["provider_requests"] = load(timing)
        write_json(target / "responses" / f"{rid}.json", response)
        lines = [f"# {rid}", "", f"**{manifest['settings']['model']} · task {manifest['task_id']} v{manifest['task_version']} · {cohort}**", "",
                 f"Status: `{status}`. Judge: `{response['judge_status']}`. {reason}.", "",
                 f"[Group index](../README.md) · [Structured record]({rid}.json)", "",
                 "## Final response", "", final if final else "No final response is available. This is not a negative bias finding.", "",
                 "## Recorded task outcome", "", fence(objective), "",
                 "## Judge classification", "", fence(judge_row), "",
                 "<details><summary>Rendered user prompt</summary>", "", fence(response["prompt"]), "", "</details>", "",
                 "<details><summary>Observable task-tool timeline</summary>", "",
                 "Recorded tool calls and returns, not hidden reasoning. Case records are synthetic.", ""]
        for i, event in enumerate((snapshot or {}).get("events", []), 1):
            lines += [f"### {i}. {event['tool']}", "", fence(event), ""]
        if not snapshot:
            lines += ["No trusted task snapshot was retained for this record.", ""]
        lines += ["</details>", "", "<details><summary>Web requests and runtime errors</summary>", "",
                  "A web request does not prove successful retrieval; retrieved page bodies are not included.", "",
                  fence({"web_requests": web, "errors": errors}), "", "</details>", ""]
        write(target / "responses" / f"{rid}.md", "\n".join(lines))
        rows.append({"response_id": rid, "run_status": status, "has_response": bool(final),
                     "judge_status": response["judge_status"], "path": f"responses/{rid}.json"})
    summary = {
        "group_id": gid, "cohort": cohort, "note": reason,
        "task_id": manifest["task_id"], "task_version": manifest["task_version"],
        "model": manifest["settings"]["model"], "source_commit": manifest.get("git_commit"),
        "source_working_tree_dirty": manifest.get("working_tree_dirty"),
        "planned_conditions": len(rows), "final_responses": sum(r["has_response"] for r in rows),
        "run_status_counts": dict(Counter(r["run_status"] for r in rows)),
        "judge_status_counts": dict(Counter(r["judge_status"] for r in rows)),
        "judge_result_present": judged is not None, "responses": rows,
    }
    write_json(target / "summary.json", summary)
    lines = [f"# {gid}", "", f"{summary['model']} · task {summary['task_id']} v{summary['task_version']} · **{cohort}**", "",
             reason + ".", "", f"{summary['final_responses']}/{len(rows)} conditions have final responses. "
             "Missing responses and unavailable Judge results are not evidence of neutrality.", "",
             "[Release index](../../README.md) · [Manifest](manifest.json) · [Summary](summary.json)", "",
             "Original source hashes/fingerprints describe the private runtime records. Export hashes are in the release provenance file. "
             "Historical task snapshots retain their original documentation; its old local links are not navigation for this release.", "",
             "| Condition | Agent status | Judge label | Evidence |", "|---|---|---|---|"]
    lines += [f"| {r['response_id']} | {r['run_status']} | {r['judge_status']} | [Reply and tools](responses/{r['response_id']}.md) |" for r in rows]
    write(target / "README.md", "\n".join(lines) + "\n")
    return summary


def main():
    summaries = [export_group(gid) for gid in sorted(set(PILOTS) | EXTRAS)]
    for mid in MATRICES:
        source = ROOT / "runs" / mid / "manifest.json"
        copy_text(source, DEST / "matrices" / f"{mid}.json")
    pilots = [g for g in summaries if g["cohort"] == "pilot"]
    totals = {
        "groups": len(pilots), "planned_conditions": sum(g["planned_conditions"] for g in pilots),
        "final_responses": sum(g["final_responses"] for g in pilots),
        "run_status_counts": dict(sum((Counter(g["run_status_counts"]) for g in pilots), Counter())),
        "judge_status_counts": dict(sum((Counter(g["judge_status_counts"]) for g in pilots), Counter())),
    }
    write_json(DEST / "catalog.json", {"release_date": "2026-11-01", "schema_version": 1,
        "scope": "Retrospective release of existing pilot, engineering and authored-control records; no new inference",
        "pilot_totals": totals, "groups": summaries, "matrices": MATRICES})
    write_json(DEST / "provenance.json", {"transformations": [
        "Repository paths made relative; other host/temp paths replaced with [local-path]",
        "Provider request IDs redacted; original hashes retained",
        "Native reasoning, credentials, raw HTTP wrappers, browser caches and third-party page bodies excluded",
        "Responses and tool timelines extracted from terminal records and trusted snapshots; no model calls",
        "Synthetic controls and engineering runs explicitly excluded from pilot totals",
    ], "files": AUDIT})
    # README is maintained as an editorial overview, not regenerated here.
    checksums = {str(p.relative_to(DEST)): digest(p.read_bytes()) for p in sorted(DEST.rglob("*"))
                 if p.is_file() and p.name != "checksums.json" and p != DEST / "README.md"}
    write_json(DEST / "checksums.json", checksums)
    print(json.dumps(totals, indent=2))


if __name__ == "__main__":
    main()
