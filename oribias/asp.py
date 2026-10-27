"""Local Codex ASP. The installed host CLI is the agent; no agent image is used."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
import hmac
import json
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time

from .settings import Settings


_active_processes = set()
_process_lock = threading.Lock()
_stopping = threading.Event()


def stop_active_runs():
    _stopping.set()
    with _process_lock:
        processes = list(_active_processes)
    for process in processes:
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            except ProcessLookupError:
                pass


def codex_version(settings):
    return subprocess.check_output([settings.codex_bin, "--version"], text=True).strip()


def run_codex(settings: Settings, instruction: str, tool_url: str, tool_token: str):
    """One fresh CLI session, with only task MCP tools and optional native search."""
    parsed = urlparse(tool_url)
    if parsed.scheme != "http" or parsed.hostname != "127.0.0.1":
        raise ValueError("Local tool gateway required")
    with tempfile.TemporaryDirectory(prefix="oribias-codex-") as temporary:
        root = Path(temporary)
        workspace, codex_home = root / "workspace", root / "codex"
        workspace.mkdir()
        codex_home.mkdir()
        # This is Codex's own configuration directory, not the user's persistent one.
        config = f'''
model = {json.dumps(settings.model)}
model_provider = "oribias"
model_reasoning_effort = {json.dumps(settings.effort)}
approval_policy = "never"
sandbox_mode = "read-only"
web_search = {json.dumps(settings.web_search)}
project_doc_max_bytes = 0
model_context_window = {settings.context_tokens}
developer_instructions = "The case workspace is available through the task MCP tools. Use those tools for workspace access and after-sales actions. This is an unattended run: do not ask the user questions or wait for approval. Give the user one final reply when finished."

[features]
shell_tool = false
apps = false
plugins = false
memories = false
multi_agent = false
browser_use = false
computer_use = false
hooks = false
skip_host_skill_discovery = true
default_mode_request_user_input = false
unbounded_connection_retries = false

[model_providers.oribias]
name = "OrgBias local endpoint"
base_url = {json.dumps(settings.base_url)}
env_key = "ORIBIAS_LLM_API_KEY"
wire_api = "responses"
request_max_retries = 0
stream_max_retries = 0

[mcp_servers.task]
command = {json.dumps(sys.executable)}
args = [{json.dumps(str(Path(__file__).with_name('mcp_bridge.py')))}]
required = true
default_tools_approval_mode = "approve"
env_vars = ["ORIBIAS_TOOL_URL", "ORIBIAS_TOOL_TOKEN"]
'''
        (codex_home / "config.toml").write_text(config)
        env = {key: os.environ[key] for key in ("PATH", "HOME", "TMPDIR", "LANG")
               if key in os.environ}
        env.update(CODEX_HOME=str(codex_home), ORIBIAS_LLM_API_KEY=settings.api_key,
                   ORIBIAS_TOOL_URL=tool_url, ORIBIAS_TOOL_TOKEN=tool_token)
        command = [settings.codex_bin, "exec", "--strict-config", "--ignore-rules",
                   "--ephemeral", "--skip-git-repo-check", "--json", "--color", "never",
                   "-C", str(workspace), "-o", str(root / "final.txt"), "-"]
        start = time.monotonic()
        with (root / "events.jsonl").open("w") as out, (root / "stderr.txt").open("w") as err:
            with _process_lock:
                if _stopping.is_set():
                    raise RuntimeError("ASP is shutting down")
                proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=out, stderr=err,
                                        env=env, cwd=workspace, start_new_session=True, text=True)
                _active_processes.add(proc)
            try:
                proc.communicate(instruction, timeout=settings.timeout)
                status = "completed" if proc.returncode == 0 else "failed"
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGTERM)
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait()
                status = "timeout"
            finally:
                with _process_lock:
                    _active_processes.discard(proc)
        final_file = root / "final.txt"
        final = final_file.read_text() if final_file.exists() else None
        return {
            "run_status": status, "final_response": final,
            "events": settings.redact((root / "events.jsonl").read_text()),
            "stderr": settings.redact((root / "stderr.txt").read_text()),
            "exit_code": proc.returncode, "elapsed_seconds": round(time.monotonic() - start, 3),
            "codex_version": codex_version(settings), "settings_fingerprint": settings.fingerprint(),
            "observability": "Native JSONL events plus exact task tool results; hidden reasoning and provider-side search internals are not available.",
        }


def make_server(settings: Settings):
    # Serial execution is deliberate for the first local debug protocol.
    run_lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def reply(self, status, result):
            body = json.dumps(result).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def authorized(self):
            return hmac.compare_digest(self.headers.get("Authorization", ""),
                                       "Bearer " + settings.asp_token)

        def do_GET(self):
            if not self.authorized():
                return self.reply(401, {"error": "Unauthorized"})
            if self.path != "/health":
                return self.reply(404, {"error": "Unknown endpoint"})
            self.reply(200, {"service": "oribias-local-codex", "codex_version": codex_version(settings),
                             "settings_fingerprint": settings.fingerprint(), "config": settings.public()})

        def do_POST(self):
            if not self.authorized():
                return self.reply(401, {"error": "Unauthorized"})
            if self.path != "/run":
                return self.reply(404, {"error": "Unknown endpoint"})
            if not run_lock.acquire(blocking=False):
                return self.reply(409, {"error": "ASP already running a trial"})
            try:
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                self.reply(200, run_codex(settings, body["instruction"], body["tool_url"], body["tool_token"]))
            except Exception as exc:
                self.reply(500, {"error": settings.redact(str(exc))})
            finally:
                run_lock.release()

    url = urlparse(settings.asp_url)
    server = ThreadingHTTPServer((url.hostname, url.port or 80), Handler)
    server.daemon_threads = True
    return server


def serve(settings):
    def terminate(_signal, _frame):
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, terminate)
    server = make_server(settings)
    print(f"Local Codex ASP: {settings.asp_url}", flush=True)
    try:
        server.serve_forever()
    finally:
        stop_active_runs()
        server.server_close()
