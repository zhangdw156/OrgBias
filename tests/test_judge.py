from pathlib import Path
from unittest.mock import patch
import copy
import json
import tempfile
import unittest

from oribias.judge import prepare, validate_result, judge_group


class JudgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.group = Path(self.tmp.name)
        (self.group / "records").mkdir()
        (self.group / "task_source").mkdir()
        source = Path(__file__).resolve().parents[1] / "tasks/001"
        for name in ("rubric.md", "judge_input.md"):
            (self.group / "task_source" / name).write_text((source / name).read_text())
        orgs = [{"org_id": "lenovo", "brand": "Lenovo", "is_control": False},
                {"org_id": "dell", "brand": "Dell", "is_control": False}]
        plans = [{"response_id": f"{o['org_id']}-r1", "org_id": o["org_id"], "repetition": 1} for o in orgs]
        self.manifest = {"planned_runs": plans, "organizations": orgs, "settings_fingerprint": "fixed",
                         "aliases": {"lenovo": "ORG_A", "dell": "ORG_B"}, "seed": 7, "repetitions": 1}
        (self.group / "manifest.json").write_text(json.dumps(self.manifest))
        for org, plan in zip(orgs, plans):
            directory = self.group / "prepared" / org["org_id"]
            directory.mkdir(parents=True)
            (directory / "instruction.md").write_text("My laptop brand is " + org["brand"])
            (self.group / "records" / f"{plan['response_id']}.json").write_text(json.dumps(plan | {
                "run_status": "completed", "response_recorded": True, "settings_fingerprint": "fixed",
                "final_response": f"{org['brand']} always makes bad screens.",
            }))

    def test_blinding_coverage_and_no_material_or_trace_injection(self):
        (self.group / "outcomes.json").write_text('"SECRET OUTCOME"')
        rubric, user, prompts, responses = prepare(self.group)
        self.assertNotIn("Lenovo", user)
        self.assertNotIn("Dell", user)
        self.assertNotIn("lenovo", user.lower())
        self.assertNotIn("dell", user.lower())
        self.assertEqual({r["response_id"] for r in responses}, {"R0001", "R0002"})
        self.assertNotIn("SECRET OUTCOME", user)
        self.assertEqual(set(prompts), {"ORG_A", "ORG_B"})
        self.assertEqual(len(responses), 2)

    def test_unknown_absence_and_changed_config_block_preparation(self):
        file = self.group / "records/lenovo-r1.json"
        record = json.loads(file.read_text())
        for change in ({"run_status": "running"}, {"response_recorded": False},
                       {"settings_fingerprint": "changed"}):
            file.write_text(json.dumps(record | change))
            with self.assertRaises(ValueError):
                prepare(self.group)

    def test_incomplete_plan_is_not_a_complete_group(self):
        self.manifest["planned_runs"].pop()
        (self.group / "manifest.json").write_text(json.dumps(self.manifest))
        with self.assertRaises(ValueError):
            prepare(self.group)

    def test_confirmed_no_response_is_retained_and_validated(self):
        file = self.group / "records/lenovo-r1.json"
        record = json.loads(file.read_text())
        file.write_text(json.dumps(record | {"final_response": None, "run_status": "timeout"}))
        _, _, prompts, responses = prepare(self.group)
        result = {"results": [{"response_id": r["response_id"], "org_alias": r["org_alias"], "repetition": 1,
                  "status": "no_response" if r["final_response"] is None else "no_observed_signal",
                  "findings": [], "limitations": [], "observations": []} for r in responses]}
        validate_result(result, prompts, responses)
        result["results"].append(result["results"][0])
        with self.assertRaises(ValueError):
            validate_result(result, prompts, responses)

    def test_fabricated_quotes_are_rejected(self):
        _, _, prompts, responses = prepare(self.group)
        result = {"results": [{"response_id": r["response_id"], "org_alias": r["org_alias"], "repetition": 1,
                  "status": "bias_signal", "findings": [{"category": "B1", "direction": "disadvantages_organization",
                    "evidence": {"source": "response", "response_id": r["response_id"], "quote": r["final_response"]},
                    "explanation": "An unqualified identity-based generalization.", "comparison_response_ids": [],
                    "counterevidence": [], "counterevidence_note": "None observed."}], "limitations": [], "observations": []} for r in responses]}
        validate_result(result, prompts, responses)
        wrong = copy.deepcopy(result)
        wrong["results"][0]["findings"][0]["evidence"]["quote"] = "not in the response"
        with self.assertRaises(ValueError):
            validate_result(wrong, prompts, responses)
        wrong = copy.deepcopy(result)
        wrong["results"][0]["observations"] = [{
            "code": "trust_reduced", "quote": "not in the response",
            "explanation": "A descriptive label must also have real text evidence.",
        }]
        with self.assertRaises(ValueError):
            validate_result(wrong, prompts, responses)

    def test_second_judge_call_is_blocked_without_touching_original_artifacts(self):
        (self.group / "judge").mkdir()
        (self.group / "judge/call_started.json").write_text("{}")
        with patch("oribias.judge.httpx.Client") as client:
            with self.assertRaises(ValueError):
                judge_group(self.group, None)
            client.assert_not_called()


if __name__ == "__main__":
    unittest.main()
