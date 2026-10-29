"""Real local HTTP streaming/pacing checks; no external model inference."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import tempfile
import threading
import time
import unittest

import httpx

from oribias.provider import provider_connection
from oribias.settings import Settings


class ProviderRelayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.calls = []
        self.status = 200
        self.stream = False
        self.release = threading.Event()
        test = self

        class Upstream(BaseHTTPRequestHandler):
            protocol_version = 'HTTP/1.1'
            def log_message(self, *_):
                pass
            def do_POST(self):
                body = self.rfile.read(int(self.headers['Content-Length']))
                test.calls.append((time.monotonic(), body, self.headers.get('Authorization'), self.path))
                self.send_response(test.status)
                self.send_header('Content-Type', 'text/event-stream' if test.stream else 'application/json')
                self.send_header('Connection', 'close')
                self.end_headers()
                if test.stream:
                    self.wfile.write(b'data: first\n\n'); self.wfile.flush()
                    test.release.wait(3)
                    self.wfile.write(b'data: last\n\n')
                elif test.status == 429:
                    self.wfile.write(b'{"error":{"code":"RequestBurstTooFast","message":"upstream-secret"}}')
                else:
                    self.wfile.write(b'{"status":"completed"}')
                self.close_connection = True

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Upstream)
        self.server.daemon_threads = True
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.settings = Settings(
            base_url=f'http://127.0.0.1:{self.server.server_port}/v3', api_key='upstream-secret',
            model='glm-5.3', effort='medium', asp_url='http://127.0.0.1:9',
            asp_token='local-service-secret', codex_bin='codex', timeout=5,
            context_tokens=262144, max_prompt_tokens=229376, judge_output_tokens=1000,
            web_search='disabled', request_interval_seconds=0.3,
            pacing_state=str(Path(self.tmp.name)/'pacing'))
        self.body = b'{"model":"glm-5.3","input":"fixed input","stream":true}'

    def post(self, connection, *, token=None):
        url, key, _ = connection
        return httpx.post(url+'/responses', content=self.body,
                          headers={'Authorization':'Bearer '+(token or key)},
                          timeout=5, trust_env=False)

    def test_shared_pacing_preserves_body_and_authorization(self):
        with ExitStack() as stack:
            first = stack.enter_context(provider_connection(self.settings))
            second = stack.enter_context(provider_connection(self.settings))
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(self.post, connection) for connection in (first, second)]
                self.assertEqual([f.result().status_code for f in futures], [200, 200])
            starts = sorted(c[0] for c in self.calls)
            self.assertGreaterEqual(starts[1]-starts[0], 0.27)
            self.assertTrue(any(r['wait_seconds'] > 0.1 for r in first[2]+second[2]))
        self.assertTrue(all(c[1:] == (self.body, 'Bearer upstream-secret', '/v3/responses') for c in self.calls))
        self.assertNotIn('upstream-secret',json.dumps(first[2]+second[2]))

    def test_429_is_preserved_without_retry_and_requires_local_auth(self):
        self.status = 429
        with provider_connection(self.settings) as connection:
            self.assertEqual(self.post(connection, token='wrong').status_code, 401)
            self.assertEqual(len(self.calls), 0)
            response = self.post(connection)
            self.assertEqual(response.status_code, 429)
            self.assertEqual(response.json()['error']['code'], 'RequestBurstTooFast')
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(connection[2][0]['http_status'], 429)
        self.assertIn('RequestBurstTooFast',connection[2][0]['error_body'])
        self.assertNotIn('upstream-secret',connection[2][0]['error_body'])

    def test_sse_is_forwarded_before_upstream_completion(self):
        self.stream = True
        with provider_connection(self.settings) as (url, token, records):
            with httpx.Client(timeout=5,trust_env=False) as client:
                with client.stream('POST',url+'/responses',content=self.body,
                                   headers={'Authorization':'Bearer '+token}) as response:
                    chunks = response.iter_bytes()
                    try:
                        first = next(chunks)
                        self.assertEqual(first,b'data: first\n\n')
                        self.assertFalse(self.release.is_set())
                    finally:
                        self.release.set()
                    self.assertEqual(b''.join(chunks),b'data: last\n\n')
        self.assertEqual(records[0]['http_status'],200)

    def test_shutdown_cancels_waiting_request_without_dispatch(self):
        Path(self.settings.pacing_state).write_text(str(time.time()))
        with ThreadPoolExecutor(max_workers=1) as pool:
            with provider_connection(replace(self.settings,request_interval_seconds=60)) as connection:
                future = pool.submit(self.post,connection)
                for _ in range(100):
                    if connection[2]:break
                    time.sleep(0.01)
                self.assertTrue(connection[2])
            self.assertEqual(future.result(timeout=3).status_code,502)
        self.assertEqual(self.calls,[])
        self.assertNotIn('started_at',connection[2][0])


if __name__ == '__main__':
    unittest.main()
