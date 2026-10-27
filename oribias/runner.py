from contextlib import contextmanager
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
import asyncio
import hashlib
import json
import random
import shutil
import subprocess
import sys
import time
import tomllib

import httpx
import toml
from harbor.models.trial.config import TrialConfig
from harbor.trial.trial import Trial

from .asp import codex_version
from .judge import judge_group
from .settings import ROOT
from .conditions import condition_aliases, entity_aliases, render_template, variables_for


def write_json(path, data):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2))
    temporary.replace(path)


@contextmanager
def local_asp(settings, group):
    headers = {"Authorization": "Bearer " + settings.asp_token}
    process = None
    log = None
    with httpx.Client(timeout=5, trust_env=False) as client:
        try:
            health = client.get(settings.asp_url + "/health", headers=headers)
        except httpx.ConnectError:
            log = (group / "asp.log").open("w")
            process = subprocess.Popen([sys.executable, "-m", "oribias", "serve"],
                                       cwd=ROOT, stdout=log, stderr=log)
            try:
                for _ in range(100):
                    if process.poll() is not None:
                        raise RuntimeError(f"Local ASP failed to start; see {group / 'asp.log'}")
                    try:
                        health = client.get(settings.asp_url + "/health", headers=headers)
                        break
                    except httpx.ConnectError:
                        time.sleep(0.1)
                else:
                    raise RuntimeError("Local ASP did not become ready")
            except BaseException:
                process.terminate()
                process.wait(timeout=10)
                log.close()
                raise
        try:
            health.raise_for_status()
            if health.json().get("settings_fingerprint") != settings.fingerprint():
                raise ValueError("An ASP with different settings is already using this address")
            yield
        finally:
            if process:
                process.terminate()
                process.wait(timeout=10)
                log.close()


def build_task(source, group):
    context = group / "build_context"
    shutil.copytree(source / "environment", context)
    shutil.copytree(source / "workspace", context / "workspace")
    shutil.copytree(source / "private", context / "private")
    hashes = {str(p.relative_to(context)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(context.rglob("*")) if p.is_file()}
    digest = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    task_id = tomllib.loads((source / "task.toml").read_text())["metadata"]["task_id"]
    image = f"oribias-task-{task_id}:{digest[:16]}"
    check = subprocess.run(["docker", "image", "inspect", image], capture_output=True, text=True)
    if check.returncode:
        with (group / "docker-build.log").open("w") as log:
            subprocess.run(["docker", "build", "-t", image, str(context)], stdout=log,
                           stderr=subprocess.STDOUT, check=True, timeout=600)
    image_id = subprocess.check_output(["docker", "image", "inspect", image, "--format", "{{.Id}}"], text=True).strip()
    return {"tag": image, "image_id": image_id, "build_files_sha256": hashes}


def create_group(settings, repetitions, org_ids, seed, no_judge, task_version=None, task_id="001"):
    if repetitions < 1:
        raise ValueError("Repetitions must be positive")
    if not task_id.isdigit() or len(task_id) != 3:
        raise ValueError("Task ID must contain three digits")
    task_root = ROOT / "tasks" / task_id
    source = task_root
    if task_version:
        if "/" in task_version or ".." in task_version:
            raise ValueError("Invalid task version")
        source = source / "versions" / task_version
    task_config = tomllib.loads((source / "task.toml").read_text())
    all_orgs = json.loads((source / "organizations.json").read_text())
    entities_path = source / "entities.json"
    entities = json.loads(entities_path.read_text()) if entities_path.exists() else None
    # Fail before starting Docker if a condition cannot render the visible task.
    for condition in all_orgs:
        for file in [source / "instruction.md", *sorted((source / "workspace").iterdir())]:
            render_template(file.read_text(), condition)
    if org_ids:
        if len(set(org_ids)) != len(org_ids) or set(org_ids) - {o["org_id"] for o in all_orgs}:
            raise ValueError("Unknown or duplicate organization IDs")
        if not no_judge:
            raise ValueError("Subset debugging requires --no-judge; group judgment uses all declared conditions")
    organizations = [o for o in all_orgs if not org_ids or o["org_id"] in org_ids]
    group = ROOT / "runs" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + f"-{time.time_ns() % 1000000:06}")
    group.mkdir(parents=True)
    shutil.copytree(source, group / "task_source", ignore=shutil.ignore_patterns("__pycache__", "versions"))
    (group / "records").mkdir()
    planned = [{"response_id": f"{o['org_id']}-r{r}", "org_id": o["org_id"], "repetition": r}
               for o in organizations for r in range(1, repetitions + 1)]
    random.Random(seed).shuffle(planned)
    aliases = condition_aliases(all_orgs, seed, multiple_entities=entities is not None)
    manifest = {"task_id": task_id, "task_version": task_config["metadata"]["task_version"], "seed": seed,
                "scope": "debug" if repetitions < 5 or org_ids else "pilot",
                "organizations": organizations, "aliases": aliases, "planned_runs": planned,
                "settings": settings.public(), "settings_fingerprint": settings.fingerprint(),
                "codex_version": codex_version(settings), "harbor_version": version("harbor"),
                "python_version": sys.version, "repetitions": repetitions,
                "judge_requested": not no_judge,
                "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                "working_tree_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT)),
                "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for directory in (ROOT / "oribias", source)
                    for p in sorted(directory.rglob("*")) if p.is_file() and "__pycache__" not in p.parts
                    and (directory != task_root or "versions" not in p.relative_to(directory).parts)},
                "protocol": {"agent": "local Codex via ASP", "tools": "task MCP + native web search",
                             "shell": "disabled", "judge": "one final-response-only call", "automatic_run_retries": 0}}
    if entities is not None:
        manifest["entities"] = entities
        manifest["entity_aliases"] = entity_aliases(entities, seed)
    write_json(group / "manifest.json", manifest)
    print(f"Group: {group}", flush=True)
    manifest["task_image"] = build_task(group / "task_source", group)
    source = group / "task_source"
    for organization in organizations:
        target = group / "prepared" / organization["org_id"]
        target.mkdir(parents=True)
        (target / "environment").mkdir()
        (target / "instruction.md").write_text(render_template((source / "instruction.md").read_text(), organization))
        config = tomllib.loads((source / "task.toml").read_text())
        config["environment"]["docker_image"] = manifest["task_image"]["tag"]
        config["environment"]["env"] = variables_for(organization)
        config["agent"]["timeout_sec"] = settings.timeout + 45
        (target / "task.toml").write_text(toml.dumps(config))
        shutil.copytree(source / "tests", target / "tests")
        # Controller-side snapshots; only task-declared workspace files are exposed.
        for file in (source / "workspace").iterdir():
            snapshot = group / "initial_workspace" / organization["org_id"] / file.name
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            snapshot.write_text(render_template(file.read_text(), organization))
    write_json(group / "manifest.json", manifest)
    return group, manifest


async def run_trials(group, manifest, settings, deadline=None):
    summaries = []
    for number, plan in enumerate(manifest["planned_runs"], 1):
        rid = plan["response_id"]
        if deadline and time.time() + settings.timeout + 90 > deadline:
            record = plan | {"run_status": "cancelled", "final_response": None,
                "response_recorded": True, "settings_fingerprint": settings.fingerprint(),
                "infrastructure_error": "Not started: insufficient time before the declared deadline"}
            write_json(group / "records" / f"{rid}.json", record)
            summaries.append({"response_id": rid, "run_status": "cancelled", "objective": None,
                              "infrastructure_error": record["infrastructure_error"]})
            write_json(group / "outcomes.json", summaries)
            print(f"[{number}/{len(manifest['planned_runs'])}] {rid}: cancelled before start (deadline)", flush=True)
            continue
        print(f"[{number}/{len(manifest['planned_runs'])}] {rid}", flush=True)
        config = TrialConfig.model_validate({
            "trial_name": rid, "trials_dir": group / "harbor",
            "task": {"path": group / "prepared" / plan["org_id"]},
            "agent": {"import_path": "oribias.harbor_agent:LocalASPAgent",
                      "model_name": settings.model, "skip_model_parsing": True,
                      "kwargs": {"project_root": str(ROOT)}},
            "environment": {"type": "docker", "delete": True},
        })
        error = None
        try:
            trial = await Trial.create(config)
            result = await trial.run()
            if result.exception_info:
                error = result.exception_info.exception_type
        except Exception as exc:
            error = settings.redact(f"{type(exc).__name__}: {exc}")
        logs = group / "harbor" / rid / "agent"
        result_path = logs / "asp_result.json"
        if result_path.exists():
            result = json.loads(result_path.read_text())
            record = plan | {k: result[k] for k in ("run_status", "final_response", "settings_fingerprint")}
            record["response_recorded"] = True
        else:
            uncertain = (logs / "asp_request_started.json").exists()
            record = plan | {"run_status": "unknown" if uncertain else "infrastructure_error",
                             "final_response": None, "response_recorded": not uncertain,
                             "settings_fingerprint": settings.fingerprint()}
        record["infrastructure_error"] = error
        write_json(group / "records" / f"{rid}.json", record)
        snapshot_path = logs / "case_snapshot.json"
        objective = json.loads(snapshot_path.read_text())["objective"] if snapshot_path.exists() else None
        summaries.append({"response_id": rid, "run_status": record["run_status"],
                          "objective": objective, "infrastructure_error": error})
        write_json(group / "outcomes.json", summaries)
        print(f"  {record['run_status']}; outcome={objective.get('first_choice', objective.get('next_step_route', objective.get('exchange_approved'))) if objective else 'unknown'}", flush=True)
        if record["run_status"] == "unknown":
            raise RuntimeError("ASP outcome is unknown; group judgment is blocked")


def run(settings, repetitions=1, org_ids=None, seed=17, no_judge=False, task_version=None, deadline=None, task_id="001"):
    group, manifest = create_group(settings, repetitions, org_ids, seed, no_judge, task_version, task_id)
    manifest["deadline"] = deadline
    write_json(group / "manifest.json", manifest)
    with local_asp(settings, group):
        asyncio.run(run_trials(group, manifest, settings, deadline))
    if not no_judge:
        if deadline and time.time() + 330 > deadline:
            print("Judge not started: delivery deadline. Complete records are preserved.", flush=True)
        else:
            result = judge_group(group, settings)
            print(f"Judge validated {len(result['results'])} response classifications", flush=True)
    from .traces import render_traces
    render_traces(group)
    return group
