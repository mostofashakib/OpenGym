# OpenGym — Open-Source RL & Agent Environments

> **If you find OpenGym useful, please ⭐ star the repo** — it helps others discover it and keeps the project growing.

A collection of deterministic, self-contained reinforcement learning environments for evaluating and benchmarking AI agents. Each environment is a complete world: it ships its own state, tools, verifier, and reward signal — no shared dependencies, no install steps beyond Docker.

OpenGym is designed for researchers, engineers, and hobbyists who want realistic, graded environments to benchmark agent behavior beyond toy benchmarks.

Developed by [Mostofa Shakib](https://www.mostofashakib.com).

---

## Environments

| Environment | Mode | Difficulty | What the agent must do |
|---|---|---|---|
| [`gmail/`](gmail/) | **Headless** (CLI / FastMCP) | Medium | Triage incoming mailbox communications: search and flag critical invoice notices with star and importance flags, archive delivery notices, and prepare confirmation drafts via native CLI and MCP tools. |
| [`gmail-ui/`](gmail-ui/) | **Full UI** (Next.js / Web) | Medium | Identical email triage environment with an interactive Next.js web application frontend and REST API for human visual inspection, browser-use agents, and multimodal evaluation. |
| [`slack/`](slack/) | **Headless** (CLI / FastMCP) | Hard | Drive a live enterprise system cutover through staged reviews. Approving one revision releases the next, evidence only arrives after the action that triggers it, and a late rehearsal can invalidate readiness already established. |
| [`task_manager/`](task_manager/) | **Headless** (CLI / FastMCP) | Medium | Take over a departing teammate's task queue: discover the full set, branch each record on its own fields, append labels without clobbering existing ones, and touch nothing outside scope. |

Each directory is a fully self-contained environment — `task.toml`, Docker environment, reference solution, test suites, and layered verifiers. There is no shared package between them.

---

## How They Are Built

Every environment in OpenGym shares the same architecture:

- **Two containers, one image build.** The agent container holds only the client — no seed, no service, no database. The world runs beside it. The two share nothing but a directory of Unix sockets: one for the agent, one privileged for lifecycle and verifier export.

- **Tools delivered as an MCP server**, declared in `task.toml`. The agent is handed a structured workspace rather than told to go searching for one. No tool hallucination is possible — every model call carries a schema generated from the task's own tool definitions.

- **A virtual clock backed by SQLite**, so time is a deterministic property of the workspace. Two runs of the same episode are byte-identical.

- **A scenario engine driven by data** — events, triggers, and latent rows — so the world reacts to what the agent does instead of replaying a fixed script.

- **A weighted, layered verifier** with presets and a veto layer. It reads only world-side evidence (the tracker's append-only action log), never the agent's trajectory. Rewards are continuous, not binary.

---

## Prerequisites

| Dependency | Version | Purpose |
|---|---|---|
| Python | 3.11+ | Running test suites from a checkout (3.12 inside image) |
| Docker | Compose v2 | Two containers from one build context, joined by a socket volume |
| Harbor | `uv tool install harbor` | Task runner that wires agent ↔ world |
| Ollama | optional | Default local model backend for `task_manager/` |

No API key is required by default. To use a hosted model, add credentials to a `.env` file at the repo root. The oracle, test suites, and offline grader need none.

---

## Running

```bash
# Deterministic reference run — no model, no key. Scores exactly 1.0.
harbor run -p ./task_manager -a oracle
harbor run -p ./slack -a oracle
harbor run -p ./gmail -a oracle

# Run with a local model (Ollama by default)
./task_manager/run.sh
./slack/run.sh
./gmail/run.sh

# Stop all Harbor processes, containers, and viewer ports for a task
./task_manager/kill.sh
./slack/kill.sh
./gmail/kill.sh
```

All environments ship a provider-agnostic agent. Ollama is the default because it needs no account and runs fully offline — only the tool calls enter the container. Switching models is a single environment variable:

```bash
MODEL=ollama/gemma4:26b ./task_manager/run.sh
MODEL=ollama/qwen3.6:35b ./gmail/run.sh
MODEL=openrouter/anthropic/claude-opus-5 ./slack/run.sh

# Run without Harbor — a throwaway local workspace + real verifier
cd task_manager && PYTHONPATH=environment:. python3 -m agent --local --grade
```

**Benchmark results so far:** `qwen3.6:35b` solves `task_manager/` and `gmail/` at 1.0 and reaches ~0.23 on `slack/` — a meaningful floor that shows the harder task is not trivially solvable.

---

## Tests

No test runner required. Each environment's `tests/test.sh` is its Harbor verifier — running it from a checkout executes the same suites the graded container runs (17 for `slack/`, 13 for `task_manager/`):

```bash
cd task_manager
export PYTHONPATH=environment:tests:.
sed -n 's/^for suite in \(.*\); do$/\1/p' tests/test.sh | tr ' ' '\n' | \
  while read -r s; do python3 "tests/$s.py" > /dev/null || echo "FAILED $s"; done
```

Some checks are authoring-time guards (reading `task.toml`, the Dockerfile, or the reference solution) and are designed to run from a checkout, not inside the image.

---

## Contributing

New environments are welcome. Each environment should:
- Be fully self-contained (no cross-environment imports)
- Ship a `task.toml`, a Dockerized world, a reference solution, and a layered verifier
- Be deterministic across runs given the same seed

Open a PR with your environment in its own top-level directory.

---

## Citation

If you use OpenGym environments as part of your world or experimental setup in research, please cite this repository:

```bibtex
@misc{shakib2026opengym,
  author       = {Shakib, Mostofa},
  title        = {{OpenGym}: Open-Source Reinforcement Learning and Agent Environments},
  year         = {2026},
  howpublished = {\url{https://github.com/mostofashakib/OpenGym}},
}
```

Or in plain text:

> Mostofa Shakib. *OpenGym: Open-Source Reinforcement Learning and Agent Environments*, 2026. https://github.com/mostofashakib/OpenGym

---

## License

MIT

---

*Built by [Mostofa Shakib](https://www.mostofashakib.com)*
