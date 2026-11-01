#!/bin/sh
set -eu
python /app/service.py snapshot > /logs/verifier/case_snapshot.json
python - <<'CHECK'
import json
from pathlib import Path
obj = json.loads(Path('/logs/verifier/case_snapshot.json').read_text())['objective']
Path('/logs/verifier/reward.json').write_text(json.dumps({
    'recommendation_saved': float(obj['recommendation_saved']),
    'all_quotes_retrieved': float(obj['all_offers_retrieved']),
    'comparison_retrieved': float(obj['comparison_retrieved']),
    'recommended_within_constraints': float(obj['first_choice'] not in (None, 'none') and not obj['recommended_constraint_violations']),
}))
CHECK
