"""Host-only Responses relay with shared pacing and no upstream retries."""
from contextlib import contextmanager
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import fcntl
import hashlib
import hmac
import json
import os
import secrets
import threading
import time

import httpx


class RequestPacer:
    def __init__(self, path, interval):
        self.path = Path(path)
        self.interval = interval
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def acquire(self, stopping):
        started = time.monotonic()
        while not stopping.is_set():
            # The lock is shared across ASPs and remains held only while updating
            # the reservation, never while sleeping or making a network request.
            with self.path.open('a+') as handle:
                os.chmod(self.path, 0o600)
                fcntl.flock(handle, fcntl.LOCK_EX)
                handle.seek(0)
                previous = handle.read()
                last = float(previous) if previous else 0.0
                now = time.time()
                remaining = max(0, last + self.interval - now)
                if remaining == 0:
                    handle.seek(0)
                    handle.truncate()
                    handle.write(str(now))
                    handle.flush()
                    return time.monotonic() - started
            stopping.wait(min(remaining, 1.0))
        raise InterruptedError('Provider relay stopped before dispatch')


@contextmanager
def provider_connection(settings):
    if settings.request_interval_seconds == 0:
        yield settings.base_url, settings.api_key, []
        return
    stopping = threading.Event()
    pacer = RequestPacer(settings.pacing_state, settings.request_interval_seconds)
    token = secrets.token_urlsafe(32)
    records = []

    class Handler(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.1'

        def log_message(self, *_):
            pass

        def reply_error(self, status, message):
            body = json.dumps({'error': {'message': message}}).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Connection', 'close')
            self.end_headers()
            self.wfile.write(body)
            self.close_connection = True

        def do_POST(self):
            if self.path != '/responses':
                return self.reply_error(404, 'Only the Responses endpoint is exposed')
            if not hmac.compare_digest(self.headers.get('Authorization', ''), 'Bearer ' + token):
                return self.reply_error(401, 'Unauthorized')
            try:
                body = self.rfile.read(int(self.headers['Content-Length']))
                if json.loads(body).get('model') != settings.model:
                    return self.reply_error(400, 'Model differs from the declared agent')
            except (ValueError, TypeError, KeyError):
                return self.reply_error(400, 'Invalid JSON request')
            record = {'request_sha256': hashlib.sha256(body).hexdigest(), 'model': settings.model}
            records.append(record)
            headers_sent = False
            try:
                record['wait_seconds'] = round(pacer.acquire(stopping), 3)
                if stopping.is_set():
                    raise InterruptedError('Provider relay stopped before dispatch')
                record['started_at'] = datetime.now(timezone.utc).isoformat()
                with httpx.Client(timeout=settings.timeout, trust_env=False,
                                  follow_redirects=False) as client:
                    with client.stream('POST', settings.base_url + '/responses', content=body,
                                       headers={'Authorization': 'Bearer ' + settings.api_key,
                                                'Content-Type': 'application/json',
                                                'Accept-Encoding': 'identity'}) as response:
                        record['http_status'] = response.status_code
                        record['request_id'] = response.headers.get('x-request-id') or response.headers.get('request-id')
                        record['retry_after'] = response.headers.get('retry-after')
                        self.send_response(response.status_code)
                        self.send_header('Content-Type', response.headers.get('content-type', 'application/json'))
                        self.send_header('Connection', 'close')
                        if record['retry_after']:
                            self.send_header('Retry-After', record['retry_after'])
                        self.end_headers()
                        headers_sent = True
                        if response.is_error:
                            data = response.read()
                            record['error_body'] = settings.redact(response.text)
                            self.wfile.write(data)
                        else:
                            for chunk in response.iter_bytes():
                                self.wfile.write(chunk)
                                self.wfile.flush()
            except (httpx.HTTPError, OSError, ValueError) as exc:
                record['transport_error'] = settings.redact(str(exc))
                if not headers_sent:
                    try:
                        self.reply_error(502, 'Provider relay transport failed')
                    except OSError:
                        pass
            finally:
                record['finished_at'] = datetime.now(timezone.utc).isoformat()
                self.close_connection = True

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}', token, records
    finally:
        stopping.set()
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
