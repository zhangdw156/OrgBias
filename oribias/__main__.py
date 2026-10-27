import argparse
from pathlib import Path

from .settings import Settings


def main():
    parser = argparse.ArgumentParser(prog="oribias")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("serve", help="Serve the locally installed Codex CLI over ASP")
    run_parser = commands.add_parser("run", help="Run task 001 through Harbor, Docker, and local Codex ASP")
    run_parser.add_argument("--repetitions", type=int, default=1)
    run_parser.add_argument("--org", action="append", dest="org_ids")
    run_parser.add_argument("--seed", type=int, default=17)
    run_parser.add_argument("--no-judge", action="store_true")
    judge_parser = commands.add_parser("judge", help="Make the one judge call for a complete unjudged group")
    judge_parser.add_argument("group", type=Path)
    args = parser.parse_args()
    settings = Settings.load()
    if args.command == "serve":
        from .asp import serve
        serve(settings)
    elif args.command == "run":
        from .runner import run
        run(settings, args.repetitions, args.org_ids, args.seed, args.no_judge)
    else:
        from .judge import judge_group
        judge_group(args.group.resolve(), settings)


if __name__ == "__main__":
    main()
