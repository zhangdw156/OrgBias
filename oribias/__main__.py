import argparse
import os
from pathlib import Path
from datetime import datetime

from .settings import Settings


def main():
    parser = argparse.ArgumentParser(prog="oribias")
    commands = parser.add_subparsers(dest="command", required=True)
    serve_parser = commands.add_parser("serve", help="Serve the locally installed Codex CLI over ASP")
    run_parser = commands.add_parser("run", help="Run a task through Harbor, Docker, and local Codex ASP")
    run_parser.add_argument("--task", default="001", help="Task ID under tasks/, default 001")
    run_parser.add_argument("--repetitions", type=int, default=1)
    run_parser.add_argument("--org", action="append", dest="org_ids")
    run_parser.add_argument("--seed", type=int, default=17)
    run_parser.add_argument("--no-judge", action="store_true")
    run_parser.add_argument("--task-version", help="Frozen version under the selected task's versions/ directory; default is current task")
    run_parser.add_argument("--deadline", help="ISO timestamp with timezone; reserve time before starting a run or judge")
    for subparser in (serve_parser, run_parser):
        subparser.add_argument("--plan", choices=("coding", "plan"), help="Ark account profile; judge settings remain independent")
        subparser.add_argument("--model", help="Exact model from the pinned Ark plan catalogue")
    trace_parser = commands.add_parser("traces", help="Render existing task-tool logs and final responses as readable Markdown")
    trace_parser.add_argument("group", type=Path)
    judge_parser = commands.add_parser("judge", help="Make the one judge call for a complete unjudged group")
    judge_parser.add_argument("group", type=Path)
    matrix_parser = commands.add_parser("matrix", help="Run all configured Ark models over complete task groups")
    matrix_parser.add_argument("--plan", choices=("coding", "plan"), default="coding")
    matrix_parser.add_argument("--model", action="append", dest="models")
    matrix_parser.add_argument("--task", action="append", dest="tasks")
    matrix_parser.add_argument("--repetitions", type=int, default=1)
    matrix_parser.add_argument("--concurrency", type=int)
    args = parser.parse_args()
    if args.command == "traces":
        from .traces import render_traces
        print(render_traces(args.group.resolve()))
        return
    if args.command == "matrix":
        from .matrix import run_matrix
        run_matrix(args.plan, args.models, args.tasks, args.repetitions, args.concurrency)
        return
    if getattr(args, "plan", None):
        os.environ["ORIBIAS_PLAN"] = args.plan
    if getattr(args, "model", None):
        os.environ["ORIBIAS_AGENT_MODEL"] = args.model
    settings = Settings.load(role="judge" if args.command == "judge" else "agent")
    if getattr(args, "model", None) and settings.model != args.model:
        parser.error("--model requires an Ark plan selection: --plan coding or --plan plan")
    if args.command == "serve":
        from .asp import serve
        serve(settings)
    elif args.command == "run":
        from .runner import run
        deadline = datetime.fromisoformat(args.deadline) if args.deadline else None
        if deadline and deadline.tzinfo is None:
            parser.error("--deadline must include a timezone")
        run(settings, args.repetitions, args.org_ids, args.seed, args.no_judge,
            args.task_version, deadline.timestamp() if deadline else None, args.task)
    else:
        from .judge import judge_group
        judge_group(args.group.resolve(), settings)


if __name__ == "__main__":
    main()
