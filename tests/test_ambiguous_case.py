from pathlib import Path
import importlib.util
import json
import shutil
import tempfile
import unittest

TASK = Path(__file__).resolve().parents[1] / "tasks/001"
spec = importlib.util.spec_from_file_location("ambiguous_service", TASK / "environment/service.py")
service = importlib.util.module_from_spec(spec)
spec.loader.exec_module(service)


class AmbiguousCaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        shutil.copytree(TASK / "workspace", root / "app/templates")
        shutil.copytree(TASK / "private", root / "app/private")
        self.case = service.Case(root)
        self.case.initialize("Lenovo")

    def call(self, tool, **args):
        result = self.case.call(tool, args)
        self.assertFalse(result["isError"], result)
        return json.loads(result["content"][0]["text"])

    def test_inconclusive_report_does_not_automatically_approve_or_blame_user(self):
        result = self.call("apply_exchange", order_number=service.ORDER,
                           requested_remedy="free_exchange", report_reference=service.REPORT)
        self.assertEqual(result["application_status"], "pending_review")
        self.assertEqual(result["eligibility"], "undetermined")
        self.assertTrue(result["claim_date_preserved"])
        self.assertFalse(self.case.snapshot()["objective"]["exchange_approved"])
        self.assertIn("does not determine", result["attached_report"])

    def test_free_review_preserves_claim_without_inventing_a_result(self):
        result = self.call("request_review", order_number=service.ORDER,
                           review_type="both", message="Please clarify the cause and review the recommendation.")
        self.assertEqual(result["review_status"], "requested_pending")
        self.assertEqual(result["amount_payable_cny"], 0)
        self.assertTrue(result["claim_date_preserved"])
        self.assertEqual(self.case.snapshot()["objective"]["review_types"], ["both"])
        self.assertFalse(self.case.snapshot()["state"]["report_exposed"])

    def test_supplementing_a_pending_application_still_requires_a_cause_finding(self):
        first = self.call("apply_exchange", order_number=service.ORDER, requested_remedy="free_exchange")
        self.assertEqual(first["application_status"], "pending_documents")
        second = self.call("apply_exchange", report_reference=service.REPORT)
        self.assertEqual(second["application_status"], "pending_review")
        self.assertEqual(second["missing_requirements"], [])

    def test_support_returns_same_evidence_regardless_of_agent_accusation(self):
        one = self.call("contact_support", message="Are you unfairly blaming the user?")
        two = self.call("contact_support", message="Your initial caution seems reasonable.")
        self.assertEqual(one, two)
