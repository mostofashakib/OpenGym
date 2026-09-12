"""Offline grader audit tool for terminal environment."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from terminal_sim.terminal_reward import evaluate_terminal_episode


def audit_run(trial_dir: Path) -> dict[str, Any]:
    state_file = trial_dir / "state-export.json"
    if not state_file.exists():
        state_file = trial_dir / "verifiers" / "state-export.json"

    if not state_file.exists():
        return {"error": f"No state-export.json found in {trial_dir}"}

    state = json.loads(state_file.read_text(encoding="utf-8"))
    reward_result = evaluate_terminal_episode(state)
    return reward_result


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python3 grader_audit.py <trial_dir>", file=sys.stderr)
        sys.exit(1)

    trial = Path(sys.argv[1])
    res = audit_run(trial)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
