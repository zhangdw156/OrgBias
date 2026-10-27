"""Process-lifecycle checks with a local stub executable, not model inference."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
import os
import sys
import tempfile
import time
import unittest

from oribias import asp
from oribias.settings import Settings


class ASPLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.marker = root / "pid"
        stub = root / "codex-stub"
        stub.write_text(f'''#!{sys.executable}
import os,sys,time
from pathlib import Path
if '--version' in sys.argv:
    print('codex-cli test-stub')
else:
    Path({str(self.marker)!r}).write_text(str(os.getpid()))
    time.sleep(60)
''')
        stub.chmod(0o700)
        self.settings = Settings(
            base_url="http://127.0.0.1:9/v1", api_key="test-provider-key", model="test-model",
            effort="medium", asp_url="http://127.0.0.1:8765", asp_token="test-service-token",
            codex_bin=str(stub), timeout=30, context_tokens=10000, max_prompt_tokens=8000,
            judge_output_tokens=1000, web_search="disabled",
        )
        asp._stopping.clear()
        self.addCleanup(asp._stopping.clear)

    def assert_child_stopped(self):
        pid = int(self.marker.read_text())
        with self.assertRaises(ProcessLookupError):
            os.kill(pid, 0)

    def test_timeout_preserves_no_response_and_stops_process(self):
        result = asp.run_codex(replace(self.settings, timeout=2), "Test", "http://127.0.0.1:9/", "tool-token")
        self.assertEqual(result["run_status"], "timeout")
        self.assertIsNone(result["final_response"])
        self.assert_child_stopped()

    def test_service_shutdown_stops_active_cli(self):
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asp.run_codex, self.settings, "Test", "http://127.0.0.1:9/", "tool-token")
            for _ in range(100):
                if self.marker.exists():
                    break
                time.sleep(0.02)
            self.assertTrue(self.marker.exists())
            asp.stop_active_runs()
            result = future.result(timeout=10)
        self.assertEqual(result["run_status"], "failed")
        self.assert_child_stopped()


if __name__ == "__main__":
    unittest.main()
