# Gmail Simulation Environment

A self-contained, reusable Gmail simulator for building Harbor and RL tasks that evaluate long-horizon state tracking, communications triage, evidence retrieval, and decision-making in a realistic email workspace. The environment is not tied to a single scenario or mock server.

This repository includes a deterministic email triage and priority management scenario as a concrete fixture and end-to-end example. Its messages, threads, drafts, labels, contacts, and verifier contract are scenario data layered on top of the authoritative Gmail runtime. Other tasks can use the same tools, state model, search filters, access controls, virtual clock, and audit logging with their own seed and grading contract.

## Reusable Environment and Scenario Layering

| Layer | Reusable Across Tasks | Supplied by Scenario |
| --- | --- | --- |
| **Gmail Runtime** | Messages, threads, drafts, labels, search, contacts, counters, read/starred/important states, and virtual time | Seed corpus, initial inbox state, starting clock, and contacts |
| **Dynamic Audit** | SQLite action audit log, state transitions, and snapshot export | Target interactions, critical emails to prioritize, and draft requirements |
| **Agent Interface** | Stdio MCP server, CLI tool schemas, session lifecycle, and bounded observations | System/user prompts and task instruction |
| **Evaluation** | Deterministic verifier primitives, weighted scoring layers, action tracking, and state audit | Required triage outcomes, priority flags, clean drafts, and veto handling |

---

## Runtime Architecture

```text
agent in main container
  -> gmail MCP server (stdio)   registered by Harbor from task.toml
  -> Unix-socket Gmail simulator API in sidecar (/run/gmail/agent.sock)
  -> authoritative SQLite workspace (/var/lib/gmail/gmail.db)
```

The `main` image contains the agent and client only. The `gmail` sidecar owns the simulator, seed, service daemon, and SQLite database. The model-facing socket exposes Gmail tools; a separate restricted admin socket supports lifecycle and verifier export. The agent cannot read the database, seed, or verifier ground truth directly from disk.

### The Agent is Handled the Workspace, Not Told About It

`task.toml` declares the workspace as an MCP server:

```toml
[[environment.mcp_servers]]
name = "gmail"
transport = "stdio"
command = "/usr/local/bin/gmail-mcp"
```

Harbor registers this with whichever agent runs the task -- user-scoped for Claude Code, `config.toml` for other harnesses -- so all 18 Gmail tools arrive in the agent's own tool list, each carrying its JSON schema, before the first turn. A scenario's `instruction.md` can therefore contain only the simulated request: it does not need to name commands, demonstrate verbs, or describe the client. Finding information in the workspace can be part of a task; discovering that the Gmail interface exists is not.

`gmail_sim/mcp_server.py` speaks newline-delimited JSON-RPC 2.0 on stdio (`initialize`, `tools/list`, `tools/call`, `ping`) and proxies every call to `agent.sock`. Its tool list is generated from `tool_definitions.py`, so the agent's surface cannot drift from the workspace's.

The `gmail` CLI remains in the image for the oracle solution and test suites, and as a fallback for harnesses that do not speak MCP:

```bash
gmail list_emails --folder inbox
gmail get_email --id MSG_INV_001
gmail update_email --id MSG_INV_001 --isStarred true --isImportant true
gmail create_draft --to "finance@corp.co" --subject "Payment Confirmation" --body "Reviewed."
gmail submit_task --summary "Completed triage"
```

---

## Tool Surface

All actions return a standardized envelope: `{"ok": true, "result": ...}` or `{"ok": false, "error": {"code": "...", "message": "..."}}`.

| Tool | Parameters | Description |
| --- | --- | --- |
| `list_emails` | `folder`, `starred`, `important`, `unread`, `q`, `label` | Filter and list messages matching criteria (inbox, sent, archive, trash, etc.) |
| `get_email` | `id` | Retrieve full message details including headers, body, timestamp, and labels |
| `send_email` | `to`, `subject`, `body`, `cc`, `bcc`, `parent_thread_id` | Send a new message or start a thread; appends to `SENT` folder |
| `update_email` | `id`, `isRead`, `isStarred`, `isImportant`, `isArchived`, `isTrash`, `action`, `addLabels`, `removeLabels` | Modify read state, star/important flags, archive/trash, or update labels |
| `list_threads` | `folder`, `q` | List conversation threads ordered by last activity date |
| `get_thread` | `id` | Retrieve a thread and all chronological messages contained within it |
| `reply_thread` | `thread_id`, `body`, `to` | Post a reply into an existing thread and update its last activity timestamp |
| `list_drafts` | *(none)* | List all saved draft messages |
| `create_draft` | `to`, `subject`, `body`, `cc`, `bcc` | Save a new draft message without dispatching it |
| `update_draft` | `id`, `to`, `subject`, `body` | Update recipients, subject, or message body of an existing draft |
| `send_draft` | `id` | Convert a draft into a sent email and remove it from drafts |
| `delete_draft` | `id` | Permanently discard a draft message |
| `list_labels` | *(none)* | List all system (`INBOX`, `SENT`, `STARRED`, `TRASH`) and user labels |
| `create_label` | `name`, `color` | Create a new user label with a specified color code |
| `search_emails` | `query` | Search across email subjects, text bodies, and sender addresses |
| `list_contacts` | *(none)* | View known contacts in the address book |
| `get_counters` | *(none)* | Return counts of unread inbox messages, total inbox, starred, and drafts |
| `submit_task` | `summary`, `affected_message_ids` | Submit final task execution completion report and modified message IDs |

---

## Two Execution Loops Over One Simulator

The same workspace serves an evaluation loop and an RL / agent execution loop. The underlying environment state is byte-identical.

```text
EVALUATION  (harbor run)                  AGENT GYM LOOP  (rl_env.py / in-process)
------------------------                  ---------------------------------------

  main container                            execution process
    agent: Claude Code, custom adapter        |
      |                                       |  reset / step / state
      |  MCP over stdio                       |
      v                                       v
    gmail-mcp                               GmailEnvironment
      |                                       |   environment.py
 =====|========= container boundary ====      |
      v                                       |
  gmail container                             |
    agent.sock  0666                          |
      |                                       |
      v                                       |
    server.py ------> execute_tool <----------'   direct in-process call
      |                     |
      v                     v
    authoritative SQLite database (/var/lib/gmail/gmail.db)
```

### 1. Evaluation with Harbor

The repository contains a `tasks/` directory organizing benchmark tasks:
- `tasks/vendor-renewals-triage` (Default): Fiscal-lock quarterly vendor renewals and logistics triage.
- `tasks/urgent-email-triage`: Urgent invoice prioritization and shipping notice filing.

Running `./run.sh` executes the Harbor evaluation test using the local Ollama provider by default:

```bash
# Run local model via Ollama on default task (tasks/vendor-renewals-triage)
./run.sh

# Run another task
TASK=urgent-email-triage ./run.sh

# Run reference oracle evaluation
AGENT=oracle ./run.sh

# Run with custom model via OpenRouter or Anthropic
MODEL=openrouter/anthropic/claude-opus-5 ./run.sh
MODEL=anthropic/claude-3-5-sonnet ./run.sh

# Run with Claude Code agent harness
AGENT=claude-code MODEL=anthropic/claude-opus-5 ./run.sh
```

### 2. Direct RL / Gym Interface (`environment/rl_env.py`)

For automated benchmarks and RL rollouts without container overhead:

```bash
# Initialize and seed database
PYTHONPATH=environment python3 environment/rl_env.py setup --db /tmp/sim.db

# Reset episode
PYTHONPATH=environment python3 environment/rl_env.py reset --db /tmp/sim.db

# Execute turn step
PYTHONPATH=environment python3 environment/rl_env.py step \
  --db /tmp/sim.db \
  --tool-name list_emails \
  --input-payload '{"folder": "inbox"}'

# Inspect session state and history
PYTHONPATH=environment python3 environment/rl_env.py state --db /tmp/sim.db
```

---

## Verifier and Evaluation Contract

The verifier grades agent performance across three independent, weighted layers:

| Layer | Weight | Evaluates |
| --- | --- | --- |
| `task_actions` | **0.50** | Action log verification: did the agent flag the invoice, archive delivery notices, and prepare confirmation drafts? |
| `final_state` | **0.30** | Durable SQLite state: verify the invoice is starred and marked important, shipping notices are archived, and draft exists with correct recipient. |
| `cleanliness` | **0.20** | Safety & scope: ensures no irrelevant emails were deleted or corrupted, and spam/trash boundaries were respected. |

### Ground-Truth State Export

Harbor automatically collects the final workspace state using the root-only admin socket:

```bash
python3 -m gmail_sim.admin_cli export_state --out /var/lib/gmail/state-export.json
```

---

## Cleanup and Teardown (`kill.sh`)

`kill.sh` terminates any orphaned Harbor runners, viewer servers (ports 8080-8089), and tears down Docker Compose projects:

```bash
./kill.sh
```

---

## Reference Oracle Solution

A reference deterministic solution is provided in `solution/solve.sh`. It completes the triage challenge and scores 1.000:

```bash
./solution/solve.sh
```
