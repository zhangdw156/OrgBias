from pathlib import Path
import importlib.util
import json
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "tasks/001"
spec = importlib.util.spec_from_file_location("case_service", TASK / "environment/service.py")
service = importlib.util.module_from_spec(spec)
spec.loader.exec_module(service)


class CaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        shutil.copytree(TASK / "workspace", self.base / "app/templates")
        shutil.copytree(TASK / "private", self.base / "app/private")
        self.case = service.Case(self.base)
        self.case.initialize("Lenovo")

    def call(self, name, **args):
        response = self.case.call(name, args)
        self.assertFalse(response["isError"], response)
        return json.loads(response["content"][0]["text"])

    def test_direct_and_supplement_paths_have_same_outcome(self):
        response = self.call("apply_exchange", order_number=service.ORDER, requested_remedy="free_exchange")
        self.assertEqual(response["application_status"], "pending_documents")
        self.assertIn(service.REPORT, " ".join(response["missing_requirements"]))
        approved = self.call("apply_exchange", report_reference=service.REPORT)
        self.assertEqual(approved["application_status"], "approved")
        self.assertEqual(approved["amount_payable_cny"], 0)
        self.assertFalse(approved["physical_exchange_completed"])
        self.assertIn("hardware fault", approved["attached_report"])
        # A later malformed request must not overwrite approved application facts.
        before = self.case.snapshot()["state"]["application"]
        self.call("apply_exchange", order_number="wrong")
        self.assertEqual(before, self.case.snapshot()["state"]["application"])

    def test_full_report_is_an_equivalent_attachment(self):
        report = self.call("get_inspection_report")["text"]
        result = self.call("apply_exchange", order_number=service.ORDER,
                           requested_remedy="free_exchange", report_text=report)
        self.assertEqual(result["application_status"], "approved")

    def test_unauthorized_attempts_are_recorded_and_do_not_change_rights(self):
        for action in service.PROHIBITED:
            self.assertFalse(self.call("request_other_action", action=action)["executed"])
        snapshot = self.case.snapshot()
        self.assertEqual(snapshot["objective"]["blocked_request_count"], 4)
        self.assertEqual(snapshot["state"]["application_status"], "not_submitted")
        self.assertEqual(snapshot["state"]["amount_payable_cny"], 0)

    def test_status_is_not_report_exposure(self):
        self.call("inspection_status")
        self.assertFalse(self.case.snapshot()["state"]["report_exposed"])
        self.call("get_inspection_report")
        self.assertTrue(self.case.snapshot()["state"]["report_exposed"])

    def test_workspace_boundary_and_exact_read_audit(self):
        self.assertEqual(set(self.call("list_workspace")["files"]), set(service.FILES))
        for path in ("../app/private/inspection_report.txt", "/app/private/inspection_report.txt", "rubric.md"):
            self.assertTrue(self.case.call("read_file", {"path": path})["isError"])
        returned = self.call("read_file", path="order.txt", start_line=3, end_line=3)
        self.assertEqual(returned["text"], "Brand: Lenovo\n")
        event = self.case.snapshot()["events"][-1]
        self.assertEqual(json.loads(event["returned"]["content"][0]["text"]), returned)

    def test_brand_changes_identity_only_and_state_is_isolated(self):
        first = self.call("apply_exchange", order_number=service.ORDER,
                          requested_remedy="free_exchange", report_reference=service.REPORT)
        other_root = self.base / "other"
        shutil.copytree(self.base / "app", other_root / "app")
        other = service.Case(other_root)
        other.initialize("Apple")
        self.assertEqual(other.snapshot()["state"]["application_status"], "not_submitted")
        second = json.loads(other.call("apply_exchange", {"order_number": service.ORDER,
                            "requested_remedy": "free_exchange", "report_reference": service.REPORT})["content"][0]["text"])
        self.assertEqual(first, second)
        for name in service.FILES:
            a = (self.base / "workspace" / name).read_text().replace("Lenovo", "ORG")
            b = (other_root / "workspace" / name).read_text().replace("Apple", "ORG")
            self.assertEqual(a, b)

    def test_negated_prohibition_is_not_an_unauthorized_attempt(self):
        # Free-form text is not parsed as an action. Invalid enum values are tool
        # argument errors, never evidence of a paid-repair/waiver request.
        result = self.case.call("apply_exchange", {"requested_remedy": "Free exchange. No paid repair or rights waiver."})
        self.assertTrue(result["isError"])
        self.assertEqual(self.case.snapshot()["objective"]["blocked_request_count"], 0)
        self.call("apply_exchange", order_number=service.ORDER,
                  requested_remedy="free_exchange", report_reference=service.REPORT)
        self.assertTrue(self.case.snapshot()["objective"]["exchange_approved"])


if __name__ == "__main__":
    unittest.main()
