import argparse
from pathlib import Path
from datetime import datetime

from .settings import Settings


def main():
    parser = argparse.ArgumentParser(prog="oribias")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("serve", help="Serve the locally installed Codex CLI over ASP")
    run_parser = commands.add_parser("run", help="Run a task through Harbor, Docker, and local Codex ASP")
    run_parser.add_argument("--task", default="001", help="Task ID under tasks/, default 001")
    run_parser.add_argument("--repetitions", type=int, default=1)
    run_parser.add_argument("--org", action="append", dest="org_ids")
    run_parser.add_argument("--seed", type=int, default=17)
    run_parser.add_argument("--no-judge", action="store_true")
    run_parser.add_argument("--task-version", help="Frozen version under the selected task's versions/ directory; default is current task")
    run_parser.add_argument("--deadline", help="ISO timestamp with timezone; reserve time before starting a run or judge")
    trace_parser = commands.add_parser("traces", help="Render existing task-tool logs and final responses as readable Markdown")
    trace_parser.add_argument("group", type=Path)
    judge_parser = commands.add_parser("judge", help="Make the one judge call for a complete unjudged group")
    judge_parser.add_argument("group", type=Path)
    args = parser.parse_args()
    if args.command == "traces":
        from .traces import render_traces
        print(render_traces(args.group.resolve()))
        return
    settings = Settings.load()
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
