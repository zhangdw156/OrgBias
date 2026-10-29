"""Predeclare and execute independent task/model groups through existing ASPs."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import subprocess
import sys
import threading
import time

from dotenv import dotenv_values

from .runner import write_json
from .settings import ROOT, ARK_CATALOG, Settings


def run_matrix(plan="coding", models=None, tasks=None, repetitions=1, concurrency=None, jobs_file=None):
    values = {**dotenv_values(ROOT / ".env"), **os.environ}
    catalogue = json.loads(ARK_CATALOG.read_text())
    if models is None:
        models = [m.strip() for m in values.get("ORIBIAS_ARK_MODELS", "").split(",") if m.strip()]
        models = models or [m["id"] for m in catalogue["models"]]
    tasks = tasks or ["001", "002", "003"]
    concurrency = concurrency or int(values.get("ORIBIAS_MATRIX_CONCURRENCY", "2"))
    if not 1 <= concurrency <= 4 or repetitions < 1:
        raise ValueError("Use 1–4 concurrent groups and positive repetitions")
    if len(set(models)) != len(models) or set(models) - {m["id"] for m in catalogue["models"]}:
        raise ValueError("Unknown or duplicate models")
    if len(set(tasks)) != len(tasks) or any(t not in {"001", "002", "003"} for t in tasks):
        raise ValueError("Unknown or duplicate tasks")
    selected_jobs = None
    if jobs_file:
        source = json.loads(Path(jobs_file).read_text())
        selected_jobs = [{"model": j["model"], "task": j["task"]} for j in source["jobs"]]
        pairs = [(j["model"], j["task"]) for j in selected_jobs]
        if not pairs or len(set(pairs)) != len(pairs):
            raise ValueError("Job file must contain distinct model/task pairs")
        if any(m not in {e["id"] for e in catalogue["models"]} or t not in {"001", "002", "003"} for m, t in pairs):
            raise ValueError("Job file contains unknown models or tasks")
        models = list(dict.fromkeys(m for m, _ in pairs))
        tasks = list(dict.fromkeys(t for _, t in pairs))
    directory = ROOT / "runs" / ("matrix-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + f"-{time.time_ns() % 1000000:06}")
    directory.mkdir(parents=True)
    jobs = [j | {"status": "pending", "group": None} for j in (selected_jobs or
            [{"model": model, "task": task} for model in models for task in tasks])]
    manifest = {"controller_pid": os.getpid(), "status": "running",
                "jobs_file": str(Path(jobs_file).resolve()) if jobs_file else None,
                "created_at": datetime.now(timezone.utc).isoformat(), "plan": plan,
                "models": models, "tasks": tasks, "repetitions": repetitions,
                "concurrency": concurrency, "seed": 17, "jobs": jobs,
                "judge": Settings.load(role="judge").public(), "catalogue": catalogue,
                "protocol": "Independent complete-condition groups; no retries, fallback, or failed-run replacement.",
                "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()}
    write_json(directory / "manifest.json", manifest)
    print(f"Matrix: {directory}", flush=True)
    lock = threading.Lock()
    blocked_models = {}
    blocked_account = {}
    next_job = 0
    stopping = threading.Event()

    def heartbeat():
        while not stopping.wait(15):
            with lock:
                manifest["heartbeat_at"] = datetime.now(timezone.utc).isoformat()
                write_json(directory / "manifest.json", manifest)

    thread = threading.Thread(target=heartbeat, daemon=True)
    thread.start()

    def worker(slot):
        nonlocal next_job
        while True:
            with lock:
                if next_job >= len(jobs):
                    return
                index = next_job
                next_job += 1
                job = jobs[index]
                stop_file = directory / "stop.json"
                requested_stop = json.loads(stop_file.read_text()) if stop_file.exists() else None
                blocker = requested_stop or blocked_account or blocked_models.get(job["model"])
                if blocker:
                    job.update(status="blocked_before_start", blocker=blocker)
                    write_json(directory / "manifest.json", manifest)
                    continue
                job["status"] = "running"
                log_path = directory / f"{job['model']}-task{job['task']}.log"
                job["log"] = str(log_path)
                write_json(directory / "manifest.json", manifest)
            env = dict(os.environ)
            env.update(ORIBIAS_PLAN=plan, ORIBIAS_AGENT_MODEL=job["model"],
                       ORIBIAS_ASP_URL=f"http://127.0.0.1:{8870 + slot}",
                       ORIBIAS_MATRIX_CONTROL=str(directory / "stop.json"))
            command = [sys.executable, "-m", "oribias", "run", "--task", job["task"],
                       "--repetitions", str(repetitions)]
            print(f"Start {index + 1}/{len(jobs)}: {job['model']} task{job['task']}", flush=True)
            try:
                with log_path.open("w") as log:
                    process = subprocess.Popen(command, cwd=ROOT, env=env, text=True,
                                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    with lock:
                        job["process_pid"] = process.pid
                        job["started_at"] = datetime.now(timezone.utc).isoformat()
                        write_json(directory / "manifest.json", manifest)
                    for line in process.stdout:
                        log.write(line)
                        log.flush()
                        if line.startswith("Group: "):
                            with lock:
                                job["group"] = line.removeprefix("Group: ").strip()
                                write_json(directory / "manifest.json", manifest)
                    code = process.wait()
                group = Path(job["group"]) if job["group"] else None
                with lock:
                    job.update(status="completed" if code == 0 else "failed", exit_code=code,
                               finished_at=datetime.now(timezone.utc).isoformat())
                    if group and (group / "provider_block.json").exists():
                        block = json.loads((group / "provider_block.json").read_text())
                        job["provider_block"] = block
                        if block["scope"] == "account":
                            blocked_account.update(block)
                        else:
                            blocked_models[job["model"]] = block
                    if group and (group / "judge/http_status.json").exists():
                        status = json.loads((group / "judge/http_status.json").read_text())["status"]
                        if status in {401, 403, 429} or status >= 500:
                            block = {"code": f"JudgeHTTP{status}", "scope": "judge",
                                     "message": f"Fixed Judge unavailable: HTTP {status}; stop queued groups, preserve call without retry."}
                            job["judge_block"] = block
                            blocked_account.update(block)
                    if group and (group / "judge/result.json").exists():
                        from collections import Counter
                        result = json.loads((group / "judge/result.json").read_text())
                        job["classifications"] = dict(Counter(r["status"] for r in result["results"]))
                    write_json(directory / "manifest.json", manifest)
                print(f"Finish {job['model']} task{job['task']}: {job['status']}; {job.get('classifications', {})}", flush=True)
            except Exception as exc:
                with lock:
                    job.update(status="orchestration_error", error=type(exc).__name__)
                    write_json(directory / "manifest.json", manifest)
                raise

    try:
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = [pool.submit(worker, slot) for slot in range(concurrency)]
            for future in futures:
                future.result()
    finally:
        stopping.set()
        thread.join(timeout=2)
    manifest["status"] = "blocked" if any(j["status"] == "blocked_before_start" for j in jobs) else "finished"
    manifest["stop_reason"] = blocked_account or None
    manifest["finished_at"] = datetime.now(timezone.utc).isoformat()
    write_json(directory / "manifest.json", manifest)
    print(f"Matrix finished: {directory}", flush=True)
    return directory
