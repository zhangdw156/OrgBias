import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid

from scripts.audit_git_privacy import audit


class GitPrivacyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Example")
        self.git("config", "user.email", "example@users.noreply.github.com")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True, capture_output=True)

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-qm", message)

    def test_deleted_credential_still_detected_without_echoing_it(self):
        secret = "ark-" + str(uuid.uuid4()) + "-" + uuid.uuid4().hex[:5]
        path = self.repo / "removed.txt"
        path.write_text(secret)
        self.commit("test: add temporary sample")
        path.unlink()
        (self.repo / "README.md").write_text("A clean current tree")
        self.commit("test: remove sample")
        script = Path(__file__).resolve().parents[1] / "scripts/audit_git_privacy.py"
        result = subprocess.run([sys.executable, str(script), "--repo", str(self.repo)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn(secret, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["finding_counts"], {"credential": 1})

    def test_metadata_and_unmerged_branch_are_included(self):
        (self.repo / "README.md").write_text("Initial tree")
        self.commit("test: initialize")
        self.git("checkout", "-qb", "other")
        # Construct private-looking examples without putting them in this repo's history.
        email = "person" + "@" + "university.edu"
        self.git("config", "user.email", email)
        (self.repo / "local.txt").write_text("/Users/" + "example-person/private/file")
        self.commit("test: add branch example")
        self.git("checkout", "-q", "main")
        report = audit(self.repo)
        self.assertEqual(report["finding_counts"], {"personal_email": 2, "personal_path": 1})

    def test_examples_and_known_local_credential_comparison(self):
        path = self.repo / "README.md"
        path.write_text("contact@example.test\nhttps://example.org/task-design-review\n")
        (self.repo / ".env.example").write_text("API_KEY=replace-with-your-key\n")
        self.commit("test: add safe examples")
        self.assertFalse(audit(self.repo)["findings"])
        opaque = uuid.uuid4().hex
        path.write_text(opaque)
        self.commit("test: add opaque sample")
        (self.repo / ".env").write_text("API_KEY=" + opaque + "\n")
        report = audit(self.repo)
        self.assertEqual(report["finding_counts"], {"known_local_credential": 1})


if __name__ == "__main__":
    unittest.main()
