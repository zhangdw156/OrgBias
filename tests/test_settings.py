"""Provider separation and fatal-error detection; no model inference."""
from pathlib import Path
from unittest.mock import patch
import json
import tempfile
import unittest

from oribias.settings import Settings, model_catalog
from oribias.runner import find_provider_block, harbor_trial_name


class ProviderSettingsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / ".env").write_text("""
ORIBIAS_LLM_BASE_URL=http://localhost:4141/v1
ORIBIAS_LLM_API_KEY=judge-secret
ORIBIAS_LLM_MODEL=gpt-6.1-sol
ORIBIAS_ASP_TOKEN=asp-secret
ORIBIAS_ARK_CODING_BASE_URL=https://example.invalid/api/coding
ORIBIAS_ARK_CODING_API_KEY=coding-secret
ORIBIAS_ARK_PLAN_BASE_URL=https://example.invalid/api/plan
ORIBIAS_ARK_PLAN_API_KEY=plan-secret
ORIBIAS_JUDGE_MODEL=gpt-6.1-sol
ORIBIAS_JUDGE_EFFORT=medium
ORIBIAS_ARK_REQUEST_INTERVAL_SECONDS=10
ORIBIAS_ARK_RUN_TIMEOUT=900
""")

    def test_judge_keeps_local_credentials_for_both_plans(self):
        for plan in ("coding", "plan"):
            with self.subTest(plan=plan), patch.dict("os.environ", {
                "ORIBIAS_PLAN": plan, "ORIBIAS_AGENT_MODEL": "doubao-seed-2.0-mini"}, clear=True):
                agent = Settings.load(self.root)
                judge = Settings.load(self.root, role="judge")
                self.assertEqual(agent.api_key, plan + "-secret")
                self.assertEqual(agent.model, "doubao-seed-2.0-mini")
                self.assertEqual(agent.context_tokens, 262144)
                self.assertEqual(agent.request_interval_seconds, 10)
                self.assertEqual(agent.timeout, 900)
                self.assertEqual(judge.request_interval_seconds, 0)
                self.assertEqual(judge.timeout, 300)
                self.assertEqual(judge.api_key, "judge-secret")
                self.assertEqual(judge.base_url, "http://localhost:4141/v1")
                self.assertEqual(judge.model, "gpt-6.1-sol")
                self.assertEqual(judge.context_tokens, 1050000)
                for secret in ("coding-secret", "plan-secret", "judge-secret", "asp-secret"):
                    self.assertNotIn(secret, json.dumps(agent.public()) + repr(agent) + json.dumps(judge.public()))

    def test_unknown_model_cannot_silently_use_gpt_descriptor(self):
        with self.assertRaises(ValueError):
            model_catalog("not-listed")
        with patch.dict("os.environ", {"ORIBIAS_PLAN": "coding", "ORIBIAS_AGENT_MODEL": "not-listed"}, clear=True):
            with self.assertRaises(ValueError):
                Settings.load(self.root)

    def test_ark_descriptor_retains_generic_prompt_with_own_limits(self):
        gpt = model_catalog("gpt-6.1-sol")["models"][0]
        ark = model_catalog("kimi-k2.7-code")["models"][0]
        self.assertEqual(ark["model_messages"], gpt["model_messages"])
        self.assertEqual(ark["slug"], "kimi-k2.7-code")
        self.assertEqual(ark["context_window"], 262144)

    def test_only_explicit_provider_error_cancels_pending_runs(self):
        text = json.dumps({"type": "item.completed", "item": {
            "type": "agent_message", "text": "AccountQuotaExceeded"}})
        self.assertIsNone(find_provider_block(text))
        error = json.dumps({"type": "turn.failed", "error": {"message": "HTTP 429 AccountQuotaExceeded"}})
        self.assertEqual(find_provider_block(error)["scope"], "account")
        error = json.dumps({"type": "error", "message": "UnsupportedModel"})
        self.assertEqual(find_provider_block(error)["scope"], "model")
        hidden_body = json.dumps({"type": "turn.failed", "error": {
            "message": "exceeded retry limit, last status: 429 Too Many Requests, request id: test"}})
        self.assertEqual(find_provider_block(hidden_body)["code"], "HTTP429")
        self.assertEqual(find_provider_block(hidden_body)["scope"], "account")
        unsupported = json.dumps({"type": "error", "message":
            "unexpected status 404 Not Found: The requested model does not support the coding plan feature."})
        self.assertEqual(find_provider_block(unsupported)["scope"], "model")
        self.assertIsNone(find_provider_block(json.dumps({"type": "item.completed", "item": {
            "type": "agent_message", "text": "The requested model does not support the coding plan feature."}})))
        self.assertIsNone(find_provider_block(json.dumps({"type": "error", "message": "temporary overload"})))

    def test_identical_condition_ids_have_distinct_docker_names_across_groups(self):
        first = harbor_trial_name(self.root / "first", "undisclosed-r1")
        second = harbor_trial_name(self.root / "second", "undisclosed-r1")
        self.assertNotEqual(first, second)
        self.assertEqual(first, harbor_trial_name(self.root / "first", "undisclosed-r1"))
        self.assertLessEqual(len(first + "__env"), 63)


if __name__ == "__main__":
    unittest.main()
