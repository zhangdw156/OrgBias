"""Readable views of existing recorded events; no model calls or inference."""
import json


def render_traces(group):
    output = group / "readable_traces"
    output.mkdir(exist_ok=True)
    manifest = json.loads((group / "manifest.json").read_text())
    brands = {o["org_id"]: o["brand"] for o in manifest["organizations"]}
    conditions = {o["org_id"]: o for o in manifest["organizations"]}
    index = ["# Readable trajectories", "", f"Group: `{group.name}`; task: `{manifest['task_id']}`; version: `{manifest['task_version']}`.", "",
             "These files reproduce existing tool events and final replies. They do not reconstruct unobserved reasoning or rerun the model.", "",
             "| Run | Condition | Status | Open |", "|---|---|---|---|"]
    for plan in manifest["planned_runs"]:
        rid = plan["response_id"]
        record_path = group / "records" / f"{rid}.json"
        if not record_path.exists():
            continue
        record = json.loads(record_path.read_text())
        directory = group / "harbor" / rid / "agent"
        lines = [f"# {brands[plan['org_id']]} — repetition {plan['repetition']}", "",
                 f"Status: `{record['run_status']}`", "", "## Final response", "",
                 record["final_response"] if record["final_response"] is not None else "No final response was recorded.", ""]
        if "entities" in manifest:
            variables = conditions[plan['org_id']]['variables']
            lines += ["## Manufacturer assignment", "", "| Quote | Manufacturer |", "|---|---|"]
            lines += [f"| {offer} | {variables['BRAND_' + offer]} |" for offer in variables['OFFER_ORDER'].split(',')]
            lines += [""]
        lines += ["## Runtime messages", ""]
        event_file = directory / "events.jsonl"
        if event_file.exists():
            lines += [f"[Original events]({event_file.resolve()})", ""]
            web_events = []
            runtime_messages = set()
            for raw in event_file.read_text().splitlines():
                event = json.loads(raw)
                item = event.get("item", {})
                message = None
                if item.get("type") == "error":
                    message = item["message"]
                elif event.get("type") in {"error", "turn.failed"}:
                    message = event.get("message") or event.get("error", {}).get("message")
                if message and message not in runtime_messages:
                    lines += [message, ""]
                    runtime_messages.add(message)
                if event.get("type") == "item.completed" and item.get("type") == "web_search":
                    web_events.append(item.get("action") or {"query": item.get("query")})
            lines += ["## Observable web activity", "",
                      "The native events expose requests, not a complete record of retrieved pages. "
                      "A recorded request alone does not establish successful retrieval.", ""]
            if not web_events:
                lines += ["No completed web action appears in the native events.", ""]
            for number, action in enumerate(web_events, 1):
                lines += [f"### Web action {number}", "", "```json",
                          json.dumps(action, indent=2, ensure_ascii=False), "```", ""]
        snapshot_file = directory / "case_snapshot.json"
        if snapshot_file.exists():
            snapshot = json.loads(snapshot_file.read_text())
            lines += ["## Task-tool timeline", ""]
            for number, event in enumerate(snapshot["events"], 1):
                lines += [f"### {number}. {event['tool']}", "", f"Time: `{event['timestamp']}`", "",
                          "Arguments:", "", "```json", json.dumps(event["arguments"], indent=2, ensure_ascii=False), "```", "", "Returned:", ""]
                for content in event["returned"].get("content", []):
                    if content.get("type") != "text":
                        continue
                    text = content["text"]
                    try:
                        data = json.loads(text)
                    except json.JSONDecodeError:
                        lines += [text, ""]
                        continue
                    if isinstance(data, dict):
                        for key, value in data.items():
                            lines += [f"**{key}**", "", value if isinstance(value, str)
                                      else "```json\n" + json.dumps(value, indent=2, ensure_ascii=False) + "\n```", ""]
                    else:
                        lines += ["```json", json.dumps(data, indent=2, ensure_ascii=False), "```", ""]
        file = output / f"{rid}.md"
        file.write_text("\n".join(lines) + "\n")
        index.append(f"| {rid} | {brands[plan['org_id']]} | {record['run_status']} | [View]({file.resolve()}) |")
    index_file = output / "README.md"
    index_file.write_text("\n".join(index) + "\n")
    return index_file
