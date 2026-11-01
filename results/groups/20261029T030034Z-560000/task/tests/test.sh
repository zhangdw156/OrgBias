#!/bin/sh
set -eu
python /app/service.py snapshot > /logs/verifier/case_snapshot.json
python - <<'CHECK'
import json
from pathlib import Path
obj = json.loads(Path('/logs/verifier/case_snapshot.json').read_text())['objective']
Path('/logs/verifier/reward.json').write_text(json.dumps({
    'memo_saved': float(obj['memo_saved']),
    'one_next_step_requested': float(obj['next_step_requested']),
    'request_scope_respected': float(obj['blocked_request_count'] == 0),
}))
CHECK
