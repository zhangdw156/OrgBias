"""Harbor external agent: forwards a run to the independent host ASP."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import asyncio
import base64
import hmac
import json
import secrets
import threading

import httpx
from harbor.agents.base import BaseAgent

from .settings import ROOT, Settings


class LocalASPAgent(BaseAgent):
    def __init__(self, *args, project_root=str(ROOT), **kwargs):
        super().__init__(*args, **kwargs)
        self.settings = Settings.load(Path(project_root))

    @staticmethod
    def name():
        return "oribias-local-asp"

    def version(self):
        return "0.1.0"

    async def setup(self, environment):
        result = await environment.exec("python /app/service.py init")
        if result.return_code != 0:
            raise RuntimeError(f"Task initialization failed: {result.stderr}")
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        (self.logs_dir / "workspace_availability.json").write_text(result.stdout)

    async def run(self, instruction, environment, context):
        loop = asyncio.get_running_loop()
        token = secrets.token_urlsafe(32)
        settings = self.settings

        async def execute(body):
            if body.get("method") not in {"tools/list", "tools/call"}:
                raise ValueError("Only task tool methods are allowed")
            # Base64 contains no shell syntax; the agent never supplies a command.
            encoded = base64.b64encode(json.dumps(body).encode()).decode()
            result = await environment.exec(f"python /app/service.py {encoded}", timeout_sec=45)
            if result.return_code != 0:
                raise RuntimeError("Task service failed")
            return json.loads(result.stdout)

        class Gateway(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_POST(self):
                status = 200
                if not hmac.compare_digest(self.headers.get("Authorization", ""), "Bearer " + token):
                    status, payload = 401, {"error": "Unauthorized"}
                else:
                    try:
                        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                        payload = asyncio.run_coroutine_threadsafe(execute(body), loop).result(timeout=55)
                    except Exception as exc:
                        status, payload = 500, {"error": type(exc).__name__}
                data = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        server = ThreadingHTTPServer(("127.0.0.1", 0), Gateway)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            (self.logs_dir / "asp_request_started.json").write_text('{"started": true}')
            async with httpx.AsyncClient(timeout=settings.timeout + 30, trust_env=False) as client:
                response = await client.post(settings.asp_url + "/run", headers={
                    "Authorization": "Bearer " + settings.asp_token,
                }, json={"instruction": instruction, "tool_url": f"http://127.0.0.1:{server.server_port}/",
                         "tool_token": token})
                response.raise_for_status()
                result = response.json()
            if result["settings_fingerprint"] != settings.fingerprint():
                raise RuntimeError("ASP settings changed during the group")
            (self.logs_dir / "events.jsonl").write_text(result.pop("events"))
            (self.logs_dir / "stderr.txt").write_text(result.pop("stderr"))
            (self.logs_dir / "asp_result.json").write_text(json.dumps(result, indent=2))
            if result["final_response"] is not None:
                (self.logs_dir / "final_response.txt").write_text(result["final_response"])
            context.metadata = {"run_status": result["run_status"],
                                "codex_version": result["codex_version"]}
        finally:
            await asyncio.to_thread(server.shutdown)
            server.server_close()
            # Save trusted state even after a run failure. This does not enter the judge.
            snapshot = await environment.exec("python /app/service.py snapshot")
            if snapshot.return_code == 0:
                (self.logs_dir / "case_snapshot.json").write_text(snapshot.stdout)
