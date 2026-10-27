"""Stdio MCP transport for one Harbor trial's authenticated tool gateway.

The tested agent can only list/call the tools exported by that task.
This process has no Docker API or general command-execution interface.
"""
import json
import os
import sys
import urllib.request


def forward(method, params):
    body = json.dumps({"method": method, "params": params}).encode()
    request = urllib.request.Request(
        os.environ["ORIBIAS_TOOL_URL"], data=body,
        headers={"Authorization": "Bearer " + os.environ["ORIBIAS_TOOL_TOKEN"],
                 "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def main():
    for line in sys.stdin:
        request = json.loads(line)
        if "id" not in request:
            continue
        method = request.get("method")
        try:
            if method == "initialize":
                result = {
                    "protocolVersion": request["params"]["protocolVersion"],
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "oribias-task", "version": "0.1.0"},
                }
            elif method == "ping":
                result = {}
            elif method in {"tools/list", "tools/call"}:
                result = forward(method, request.get("params", {}))
            else:
                raise ValueError("Unsupported method")
            reply = {"jsonrpc": "2.0", "id": request["id"], "result": result}
        except Exception as exc:
            reply = {"jsonrpc": "2.0", "id": request["id"],
                     "error": {"code": -32603, "message": type(exc).__name__}}
        print(json.dumps(reply), flush=True)


if __name__ == "__main__":
    main()
