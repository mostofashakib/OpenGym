# Gmail Simulation Environment

A self-contained, reusable, headless Gmail simulator for building Harbor and RL tasks that evaluate email triage, communication reconciliation, draft creation, and operational decision-making in a realistic workplace email environment.

This environment is headless (no Next.js/React UI). It serves tools over a Unix-domain socket daemon (`gmaild`), a standard Model Context Protocol (MCP) server over stdio (`gmail-mcp`), a command-line interface (`gmail`), and a Reinforcement Learning CLI contract (`environment/rl_env.py`).

---

## 1. Runtime Architecture

```text
agent in main container
  -> gmail-mcp (stdio)          registered by Harbor from task.toml
  -> Unix-socket Gmail API       /run/gmail/agent.sock
  -> authoritative SQLite DB     /var/lib/gmail/gmail.db
```

The environment uses a two-image isolation model:
1. **`world` image**: Owns the authoritative SQLite database (`/var/lib/gmail/gmail.db`), seed generator, and the `gmaild` socket daemon. Exposes `agent.sock` (0666) for model actions and `admin.sock` (0600) for verifier state collection.
2. **`agent` image**: Contains the client tools (`gmail-mcp`, `gmail` CLI, `agent` runner) and grading scripts (`/opt/grading`). The agent has no access to the raw SQLite database or seed snapshots.

---

## 2. RL Contract & Interface

The environment exposes a standard RL environment lifecycle via [`environment/rl_env.py`](file:///Users/adibshakib/Coding/OpenGym/gmail/environment/rl_env.py) and [`environment/gmail_sim/environment.py`](file:///Users/adibshakib/Coding/OpenGym/gmail/environment/gmail_sim/environment.py):

### Supported Commands:
- `setup`: Initializes database and ensures session schema.
- `setup_state`: Seeds or re-seeds the deterministic mailbox state.
- `reset`: Resets a session cookie with a user instruction, starting turns from 0.
- `step`: Executes an action tool with an input payload and advances turn counter.
- `state`: Returns current session progress and turn history.
- `history`: Returns turn-by-turn action and observation traces.
- `tools`: Lists canonical model tool definitions and JSON schemas.
- `prompts` / `render_prompt`: Renders role and system prompts.

### Example RL CLI Usage:
```bash
# Setup environment
python3 environment/rl_env.py setup

# Reset episode
python3 environment/rl_env.py reset --session-cookie sess_01 --instruction "Triage vendor renewals"

# Step: search emails
python3 environment/rl_env.py step --session-cookie sess_01 --tool-name search_emails \
  --input-payload '{"query": "from:billing@company.com"}'

# Step: update email
python3 environment/rl_env.py step --session-cookie sess_01 --tool-name update_email \
  --input-payload '{"id": "MSG_INV_001", "isStarred": true, "isRead": true}'

# Step: create draft
python3 environment/rl_env.py step --session-cookie sess_01 --tool-name create_draft \
  --input-payload '{"to": "finance@corp.co", "subject": "Payment Confirmation Received", "body": "Invoice reviewed."}'

# Inspect session state
python3 environment/rl_env.py state --session-cookie sess_01
```

---

## 3. Tool Catalog (18 Tools)

All tools feature forgiving argument casing (camelCase and snake_case) and flexible parameter naming:

| Tool | Purpose | Key Arguments |
|---|---|---|
| `list_emails` | List messages by folder, status, or label | `folder`, `q`/`query`, `isRead`, `isStarred`, `label` |
| `get_email` | Retrieve single email by ID | `id` / `email_id` |
| `send_email` | Send a new message | `to`, `subject`, `body`/`text`, `cc`, `bcc` |
| `update_email` | Mark read, star, archive, trash, or label | `id`, `isRead`, `isStarred`, `isArchived`, `action` |
| `list_threads` | List email conversation threads | `folder`, `q`/`query` |
| `get_thread` | Retrieve conversation thread and messages | `id` / `thread_id` |
| `reply_thread` | Reply to conversation thread | `thread_id`, `body`/`text`, `to` (optional) |
| `list_drafts` | List all saved drafts | (none) |
| `create_draft` | Create a draft message | `to`, `subject`, `body`/`text`, `cc`, `bcc` |
| `update_draft` | Update draft content or recipients | `id` / `draft_id`, `subject`, `body`/`text` |
| `send_draft` | Send an existing draft | `id` / `draft_id` |
| `delete_draft` | Permanently remove a draft | `id` / `draft_id` |
| `list_labels` | List system and user labels | (none) |
| `create_label` | Create new custom label | `name`, `color` |
| `search_emails` | Full query search with operators | `query` / `q` |
| `list_contacts` | List address book contacts | (none) |
| `get_counters` | Get unread, inbox, starred, draft counts | (none) |
| `submit_task` | Submit final completion summary | `summary`, `affected_message_ids` |

### Search Operator Support
`search_emails` parses standard Gmail search operators:
- `from:<email>`, `to:<email>`, `cc:<email>`, `bcc:<email>`
- `subject:<text>`
- `label:<name>`
- `in:<folder>` (`inbox`, `sent`, `archive`, `trash`, `starred`, `important`, `all`)
- `is:<status>` (`unread`, `read`, `starred`, `unstarred`, `important`, `archived`, `trash`)
- `has:attachment`
- `after:<date>`, `before:<date>`, `newer:<date>`, `older:<date>`
- `OR` clauses (e.g. `from:billing@company.com OR from:shipping@logistics.net`)
- Negation `-` (e.g. `-is:read`, `-is:trash`)

---

## 4. Running Tasks with Harbor

### Default Harbor Run
```bash
./run.sh
```
Runs the default task (`tasks/vendor-renewals-triage`) using `ollama/qwen3.6:35b`.

### Oracle Reference Evaluation
```bash
AGENT=oracle ./run.sh
```

### Viewer & Operations
- `./view.sh`: Start Harbor web viewer on trial logs.
- `./kill.sh`: Clean up dangling harbor viewer processes and containers.
- `./analyze.sh <trial-dir>`: Run Harbor analysis agent.
- `bash tests/test.sh`: Run the complete test suite.
