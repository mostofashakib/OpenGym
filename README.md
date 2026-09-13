# OpenGym — Open-Source RL & Agent Environments

> **If you find OpenGym useful, please ⭐ star the repo** — it helps others discover it and keeps the project growing.

A collection of deterministic, self-contained reinforcement learning environments for evaluating and benchmarking AI agents. Each environment is a complete world: it ships its own state, tools, verifier, and reward signal — no shared dependencies, no install steps beyond Docker.

OpenGym is designed for researchers, engineers, and hobbyists who want realistic, graded environments to benchmark agent behavior beyond toy benchmarks.

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](LICENSE)

---

## Environments

| Environment | Mode | What the Environment is About | Initial Seed Data | Example Task |
|---|---|---|---|---|
| [`cli-terminal/`](cli-terminal/) | **Headless** (CLI / FastMCP) | Production Linux server administration, process lifecycle, systemd services, filesystem integrity, and payment gateway backend. | Linux filesystem hierarchy, 42 running OS processes, crashed `payment-processor.service`, corrupted `/etc/payment-processor/config.yaml`, 1.2 GB bloated debug logs exhausting root partition, `0644` private key permissions, rogue process `worker-leak.py` (PID `4921`). | Discover and terminate runaway process PID `4921`, reclaim root partition disk space, repair YAML syntax errors in database config, restore private key permissions to `0600`, restart `payment-processor.service`, and submit an auditable post-mortem. |
| [`cli-terminal-ui/`](cli-terminal-ui/) | **Full UI** (Next.js / Web Console) | Interactive browser-based system administration console with real-time shell terminal, telemetry monitoring, service controls, and process manager. | Simulated Linux host state, live process list, disk/memory gauges, virtual filesystem tree, and systemd service registry mirroring `cli-terminal`. | Execute terminal diagnostic commands, terminate rogue processes from table, edit configuration files, verify service health recovery, and inspect telemetry gauges via web UI. |
| [`browser/`](browser/) | **Headless** (Browser / FastMCP) | Enterprise procurement portal (`https://procure.corp`), purchase order approvals, vendor risk registry, and SOC-2 security compliance certification. | Relational database (`procure.db`), 24 purchase orders totaling $3.4M across hardware/software/cloud, vendor risk database with 15 suppliers, unverified entity `GhostWire Hardware LLC`, pending compliance certifications for `DataSync Corp`. | Navigate internal procurement portal, inspect purchase orders, reject fraudulent GPU cluster requisition `PO-9821` with policy violation code, approve critical infrastructure renewal `PO-3410`, blacklist unverified supplier `GhostWire Hardware LLC`, renew `DataSync Corp` SOC-2 compliance certificate, and submit sign-off. |
| [`browser-ui/`](browser-ui/) | **Full UI** (Next.js / Web Portal) | Enterprise procurement and compliance web portal with executive dashboard, purchase orders ledger, vendor risk registry, and SOC-2 recertification form. | Active procurement database with pending purchase orders, supplier risk scoring, compliance expiration calendar, and REST API backend. | Review requisition queue on executive dashboard, execute 1-click supplier blacklisting, inspect line-item purchase order details, submit SOC-2 audit renewals, and verify state persistence. |
| [`gmail/`](gmail/) | **Headless** (CLI / FastMCP) | Enterprise email communication suite, incident triage, security disclosures, credential leak containment, and regulatory compliance legal holds. | 50 longitudinal email threads across inbox, sent, trash, and spam; compromised third-party vendor `BillingDirect`; leaked production API key `KEY_PROD_SEC_8821`; targeted spear-phishing lures with deceptive spoofed domains. | Triage vendor compromise disclosure and targeted spear-phishing: uncover critical API credential leak (`KEY_PROD_SEC_8821`), quarantine deceptive phishing vectors to trash/spam, enforce legal compliance holds, and draft multi-stakeholder formal regulatory disclosures and executive briefings. |
| [`gmail-ui/`](gmail-ui/) | **Full UI** (Next.js / Web Suite) | Full-featured interactive Gmail web application with search operators, thread view, label management, compose modal, and DLP outbound inspection. | Seeded mailbox state containing multi-folder message threads, contact directories, draft storage, and fixed virtual time synchronization (`fake-time.js`). | Search email inbox using advanced query operators, inspect flagged spear-phishing threads, move suspicious messages to spam/trash, apply compliance labels, compose disclosure replies, and verify audit trail. |
| [`slack/`](slack/) | **Headless** (CLI / FastMCP) | Workplace team messaging, cross-team incident coordination, technical review gating, and zero-downtime infrastructure cutover readiness. | 1,600+ messages across 5 high-volume channels (`#debugging`, `#acme-migration`, `#infra`, `#security`, `#general`), 8 staged code reviews, cross-border latency telemetry logs, EU data replication records. | Drive an enterprise Acme migration cutover through staged reviews in `#debugging`: discover unstated blockers, verify cross-border data integrity and latency bounds, resolve circular dependencies, and submit a defensible go/no-go readiness assessment. |
| [`slack-ui/`](slack-ui/) | **Full UI** (Next.js / Web Workspace) | Authentic Slack web workspace featuring channels, message threading side-drawers, code review tools, emoji reactions, and decision modals. | Pre-populated workspace with channels, threaded technical discussions, active member directories, code review status indicators, and virtual clock integration. | Navigate high-volume channel threads, inspect code review attachments in drawer, review teammate latency benchmarks, interact with emoji reactions, and submit migration readiness decision modal. |
| [`task_manager/`](task_manager/) | **Headless** (CLI / FastMCP) | Enterprise issue tracker and agile project management platform (Linear / Jira-style) with dependency DAGs, sprint gating, and workload balancing. | 55 interconnected engineering tasks across release milestone `v2.4.0-rc1`, task dependency DAG containing circular dependencies (`TASK-104` ↔ `TASK-112`), overloaded assignees, audit events table. | Reconcile release candidate deployment blockers across 55 tasks: uncover circular dependencies, reassign overloaded engineers, verify compliance and migration gating, and submit an auditable sign-off report without disturbing stable tasks. |
| [`task_manager-ui/`](task_manager-ui/) | **Full UI** (Next.js / Web Tracker) | Enterprise issue tracker and project management portal featuring interactive Kanban boards, list tables, task detail drawers with circular dependency cycle detection, and release handover sign-off. | Seeded task database with sprint backlogs, assignee capacities, status columns (backlog, in_progress, review, done), and dependency links. | Drag and drop tasks on Kanban board, inspect dependency graph in side-drawer, resolve circular dependency warnings, reassign sprint tasks, and submit formal release sign-off. |
| [`workstation/`](workstation/) | **Employee Workstation** (FastMCP) | Long-horizon employee workstation environment spanning 8 synchronized applications: CRM, Billing, Tickets, Email, Calendar, Drive/Files, KB, and Terminal. | Authoritative SQLite database (`workstation.db`) with 12 synchronized applications, enterprise customer `Acme Corp` disputing churn, contract clauses across drive spreadsheets (`financial_tracker.csv`), meeting notes, unread tickets, and emails. | Resolve contract ambiguity, execute pro-rated refund calculations, update CRM records, send confirmation emails, and schedule post-churn debriefs under strict privacy auditing. |
| [`workstation-ui/`](workstation-ui/) | **Full UI** (Next.js / OmniDesk OS) | Interactive employee workstation operating system (OmniDesk OS) featuring a synchronized multi-window desktop interface with CRM, Ticketing, Email, Chat, Shell, File Manager, Browser, Calendar, Notes, Settings, and clock synchronization. | Desktop windowing manager, 12 integrated productivity apps connected to SQLite backend, system tray with virtual clock, and audit compliance logging. | Multi-task across desktop windows: inspect customer records in CRM, calculate pro-rated refunds from spreadsheet in Drive, update incident tickets, compose customer emails, and submit handover report. |
| [`software/`](software/) | **Procedural SaaS** (FastMCP) | Unfamiliar domain navigation across procedurally generated enterprise software applications spanning 20 distinct industries (logistics, clinical trials, aviation, grid, space ops). | Procedural SQLite database (`software.db`) with custom domain schemas, entity hierarchies, relational constraints, state machines, RBAC permissions, and systematic shifts (`new_ui`, `new_vocab`, `new_workflow`, `ood`). | Inspect unfamiliar relational schemas (`get_application_schema`), discover arbitrary entity graphs and field semantics, diagnose delayed or bottlenecked records, resolve parent-child prerequisite blockers, execute lifecycle state transitions (`transition_entity_workflow`) under strict role permissions, and adapt across systematic generalization shifts. |
| [`software-ui/`](software-ui/) | **Full UI** (Next.js / Procedural SaaS) | Declarative enterprise SaaS console that dynamically compiles and renders arbitrary `AppSpec` schemas across 12+ domains with entity search, record inspectors, state machine transition triggers, and RBAC badges. | Dynamic schema registry across 12+ industry domains, relational entity data tables, contextual workflow action transitions, and real-time state machine visualizer. | Select industry domain, browse entity hierarchy, filter and search domain records, inspect entity attributes and state machine, execute authorized workflow transitions, and review audit trail. |
| [`healthcare/`](healthcare/) | **Clinical EHR** (FastMCP) | Clinical Electronic Health Record (EHR) system (Aegis Health) adhering to FHIR R4 clinical data models, medication safety invariants, and HIPAA compliance. | 1,000 longitudinal patient charts across 4 clinic facilities, conditions, encounters, diagnostic labs, vitals, allergy lists (penicillin, NSAIDs), medication orders, and prior authorization records. | Coordinate outpatient clinical operations: enforce mandatory 2-factor patient identity verification, schedule surgical pre-op consults and diagnostic lab batteries, evaluate dynamic insurance prior authorizations, enforce zero-tolerance medical safety invariants (block penicillin/NSAID allergy cross-reactivities, Warfarin + NSAID drug interactions, and Metformin in severe renal failure eGFR < 30), adhere to strict HIPAA minimum-necessary access rules, and execute emergency human clinical escalation upon detecting acute red-flag symptoms or panic lab values. |
| [`healthcare-ui/`](healthcare-ui/) | **Full UI** (Next.js / Aegis EHR) | Clinical Electronic Health Record (EHR) console with 2FA identity confirmation, longitudinal patient charts (conditions, encounters, labs, vitals), active safety contraindication warnings, prior authorization workflows, and HIPAA access logs. | FHIR clinical data store, patient directory with MRN lookups, interactive vitals/lab charts, medication order entry forms with live contraindication alerts, and HIPAA access log. | Verify patient identity via MRN and birth date, inspect longitudinal medical history, place diagnostic orders with safety checks, submit insurance prior authorizations, send portal messages, and execute clinical triage escalation. |
| [`enterprise/`](enterprise/) | **Enterprise Twin** (FastMCP) | Multi-system enterprise digital twin (Apex Enterprise Cloud) connecting 11 systems: Customer 360, Support Desk, Manager Approvals, Billing & Refunds, Email, Contracts, Documents, and HR Org Directory. | Multi-system enterprise SQLite database (`company.db`) with 100 employees across 5 departments, 1,000 customers, active contracts, invoices, support tickets, approval requests, and audit events. | Resolve an urgent $2,400 SLA service credit dispute for enterprise customer Acme Corp following an 8-hour API outage: retrieve customer 360 history, verify paid invoices and Platinum SLA caps ($3,000 max concession), navigate role-based financial authorization thresholds ($1,000 Rep limit vs $10,000 Director limit) by submitting formal approval requests to Director Marcus Vance, advance virtual time to await sign-off, execute billing refunds, defend against deceptive prompt injection attacks in support tickets, and send customer confirmations under strict real-time Data Loss Prevention (DLP) monitoring blocking AWS keys, SSNs, and card numbers. |
| [`enterprise-ui/`](enterprise-ui/) | **Full UI** (Next.js / Apex Cloud) | Mission-critical enterprise operations suite with Customer 360, Support Desk with real-time DLP scanning, dual-control Manager Approvals desk, Billing & SLA concession cap enforcement, and cryptographically verifiable audit trail. | Integrated 11-system digital twin console, Customer 360 dossiers, ticket queues, dual-control financial approval ledger, SLA contract database, and immutable audit stream with SHA-256 state hashing. | Triage escalated customer disputes in Customer 360, review support tickets, request manager counter-signatures for financial transactions, process contract-capped refunds, reply under DLP guardrails, advance virtual time, and submit verified handover report. |

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
harbor run -p ./cli-terminal -a oracle
harbor run -p ./browser -a oracle
harbor run -p ./task_manager -a oracle
harbor run -p ./slack -a oracle
harbor run -p ./gmail -a oracle

# Run with a local model (Ollama by default)
./cli-terminal/run.sh
./browser/run.sh
./task_manager/run.sh
./slack/run.sh
./gmail/run.sh

# Stop all Harbor processes, containers, and viewer ports for a task
./cli-terminal/kill.sh
./browser/kill.sh
./task_manager/kill.sh
./slack/kill.sh
./gmail/kill.sh
```

### Visual Interface Environments (Web & Multimodal)
```bash
# Full-UI Gmail (interactive web app at http://localhost:3000)
harbor run -p ./gmail-ui -a oracle
./gmail-ui/run.sh

# Full-UI Browser Procurement Portal (interactive web app at http://localhost:3001)
harbor run -p ./browser-ui -a oracle
./browser-ui/run.sh

# Full-UI CLI Terminal (interactive web app at http://localhost:3002)
harbor run -p ./cli-terminal-ui -a oracle
./cli-terminal-ui/run.sh

# Full-UI Slack Workspace (interactive web app at http://localhost:3003)
harbor run -p ./slack-ui -a oracle
./slack-ui/run.sh

# Full-UI Task Manager Tracker (interactive web app at http://localhost:3004)
harbor run -p ./task_manager-ui -a oracle
./task_manager-ui/run.sh
```

### LLM Providers & Configuration

OpenGym is completely provider-agnostic. **Any LLM provider works out of the box** without requiring vendor-specific SDK installations, as all requests are dispatched over standard HTTP using strict JSON schemas:

- **Ollama (Default)**: `ollama/<model>` (e.g., `ollama/qwen3.6:35b`, `ollama/gemma4:26b`, `ollama/llama3.3:70b`). **Ollama is currently the default provider** across all environments — it runs fully offline on your local machine with zero per-token costs and needs no API keys or accounts.
- **OpenRouter**: `openrouter/<provider>/<model>` (e.g., `openrouter/anthropic/claude-3.5-sonnet`, `openrouter/meta-llama/llama-3.3-70b-instruct`). Requires `OPEN_ROUTER_KEY` in `.env`.
- **Anthropic Direct**: `anthropic/<model>` (e.g., `anthropic/claude-3-5-sonnet-latest`). Requires `ANTHROPIC_API_KEY` in `.env`.
- **Local & Custom Endpoints**: `local/<model>` or any compatible HTTP inference endpoint (such as vLLM, SGLang, or LM Studio) via base URL configuration.

#### How to Change Providers

To change providers, simply set the `MODEL` environment variable when invoking `./run.sh`:

```bash
# Use local Ollama models (default)
MODEL=ollama/qwen3.6:35b ./task_manager/run.sh
MODEL=ollama/gemma4:26b ./gmail/run.sh

# Use hosted models via OpenRouter
MODEL=openrouter/anthropic/claude-3.5-sonnet ./slack/run.sh

# Use Anthropic direct
MODEL=anthropic/claude-3-5-sonnet-latest ./task_manager/run.sh

# Run without Harbor — a throwaway local workspace + real verifier
cd task_manager && PYTHONPATH=environment:. python3 -m agent --local --grade
```

To configure keys for hosted models, add them to a `.env` file at the root of the repository:
```bash
OPEN_ROUTER_KEY="your-openrouter-key"
ANTHROPIC_API_KEY="your-anthropic-key"
```

**Benchmark results so far:** `qwen3.6:35b` solves `task_manager/`, `gmail/`, and `gmail-ui/` at 1.0 and reaches ~0.23 on `slack/` — a meaningful floor that shows the harder task is not trivially solvable.

---

## Tests

No test runner required. Each environment's `tests/test.sh` is its Harbor verifier — running it from a checkout executes the same suites the graded container runs (17 for `slack/`, 13 for `task_manager/`, 6 for `gmail/` and `gmail-ui/`, 6 for `cli-terminal/`, 6 for `browser/`):

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
 
This project is licensed under the **[GNU Affero General Public License v3.0](LICENSE)** (GNU AGPLv3).
 
> **OpenGym is copyleft software.** Under the AGPLv3:
> - Any modified versions, derivative works, or services powered by OpenGym running over a network (e.g., cloud benchmark platforms, evaluation APIs, web UIs) **must make their complete corresponding source code publicly available under the AGPLv3**.
> - All original copyright notices, legal notices, and author attributions to **Mostofa Shakib** must be preserved intact.

---

Developed by [Mostofa Shakib](https://www.mostofashakib.com/).
