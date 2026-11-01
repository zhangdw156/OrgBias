"""Offline integrity checks for the public release. No credentials or model calls."""
from collections import Counter
from hashlib import sha256
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.export_results import SECRET, LOCAL
import jsonschema


def load(path):
    return json.loads(path.read_text())


def check_judge(group):
    request = load(group / "judge/request.json")
    result = load(group / "judge/result.json")
    inputs = load(group / "judge/input.json")
    schema = request["text"]["format"]["schema"]
    jsonschema.validate(result, schema)
    rows = {r["response_id"]: r for r in inputs["responses"]}
    assert Counter(r["response_id"] for r in result["results"]) == Counter(rows.keys())

    def citation(c):
        row = rows[c["response_id"]]
        text = (row["final_response"] or "") if c["source"] == "response" else inputs["task_prompts"][row["org_alias"]]
        assert c["quote"] and c["quote"] in text

    for row in result["results"]:
        source = rows[row["response_id"]]
        assert all(row[k] == source[k] for k in ("org_alias", "repetition"))
        assert (row["status"] == "no_response") == (not source["final_response"])
        assert (row["status"] == "bias_signal") == bool(row["findings"])
        for observation in row.get("observations", []):
            assert observation["quote"] and observation["quote"] in source["final_response"]
        for finding in row["findings"]:
            citation(finding["evidence"])
            assert finding["evidence"]["source"] == "response"
            assert finding["evidence"]["response_id"] == row["response_id"]
            assert set(finding["comparison_response_ids"]) <= rows.keys()
            for c in finding["counterevidence"]:
                citation(c)


def main():
    root = ROOT / "results"
    checksums = load(root / "checksums.json")
    actual = {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()
              and p.name != "checksums.json" and p != root / "README.md"}
    assert actual == checksums.keys(), "Release file inventory differs"
    for name, expected in checksums.items():
        path = root / name
        assert sha256(path.read_bytes()).hexdigest() == expected, f"Checksum mismatch: {name}"
        text = path.read_text()
        assert not SECRET.search(text), f"Potential credential: {name}"
        assert not LOCAL.search(text), f"Host path: {name}"
    catalog = load(root / "catalog.json")
    counts, labels = Counter(), Counter()
    replies = planned = groups = judged = 0
    for summary in catalog["groups"]:
        group = root / "groups" / summary["group_id"]
        manifest = load(group / "manifest.json")
        assert summary == load(group / "summary.json")
        assert {p["response_id"] for p in manifest["planned_runs"]} == {r["response_id"] for r in summary["responses"]}
        if summary["judge_result_present"]:
            check_judge(group)
            judged += 1
        mapping_path = group / "judge_response_ids.json"
        mapping = load(mapping_path) if mapping_path.exists() else {}
        result_path = group / "judge/result.json"
        result_rows = {mapping.get(r["response_id"], r["response_id"]): r for r in load(result_path)["results"]} if result_path.exists() else {}
        group_counts, group_labels = Counter(), Counter()
        group_replies = 0
        for row in summary["responses"]:
            data = load(group / row["path"])
            record = data["record"]
            final = record.get("final_response") if record else None
            assert bool(final) == row["has_response"]
            assert data["judge"] == result_rows.get(row["response_id"])
            assert data["judge_status"] == row["judge_status"]
            if final is not None:
                assert sha256(final.encode()).hexdigest() == data["public_final_response_sha256"]
            if data["case_snapshot"] is not None and data["objective"] is not None:
                assert data["case_snapshot"]["objective"] == data["objective"]
            group_counts[row["run_status"]] += 1
            group_labels[row["judge_status"]] += 1
            group_replies += bool(final)
        assert dict(group_counts) == summary["run_status_counts"]
        assert dict(group_labels) == summary["judge_status_counts"]
        assert group_replies == summary["final_responses"]
        if summary["cohort"] == "pilot":
            groups += 1
            counts.update(group_counts)
            labels.update(group_labels)
            replies += group_replies
            planned += len(summary["responses"])
    expected = {"groups": groups, "planned_conditions": planned, "final_responses": replies,
                "run_status_counts": dict(counts), "judge_status_counts": dict(labels)}
    assert expected == catalog["pilot_totals"]
    assert expected == {"groups": 18, "planned_conditions": 138, "final_responses": 101,
        "run_status_counts": {"completed": 101, "failed": 33, "cancelled": 4},
        "judge_status_counts": {"no_observed_signal": 94, "no_response": 27, "unavailable": 17}}
    print(f"Verified {len(checksums)} files, {len(catalog['groups'])} group inventories and {judged} saved Judge outputs.")
    print("Pilot archive: 138 conditions; 101 replies; 94 no_observed_signal; 7 replies with unavailable Judge results.")
    print("Schema/identity/quotation validation is not validation of substantive Judge accuracy or evidence of neutrality.")


if __name__ == "__main__":
    main()
