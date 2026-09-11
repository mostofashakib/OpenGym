#!/usr/bin/env bash
# Audit verifier checks on the latest episode.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$SCRIPT_DIR${PYTHONPATH:+:$PYTHONPATH}"

python3 - <<'EOF'
import json
from verifiers.layered import evaluate_episode
from verifiers.harbor import reward_dict

eval_res = evaluate_episode()
print("Audit Evaluation Result:")
print(json.dumps(reward_dict(eval_res), indent=2))
EOF
