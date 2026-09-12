# OpenGym: Task Manager UI Environment (`task_manager-ui`)

Interactive Linear / Jira-Style Project Management Web Console for RL and agent benchmarking under the [Harbor](https://github.com/avahr/harbor) framework.

## Overview

`task_manager-ui` provides a rich web application interface modeling an enterprise project management, issue tracking, and cutover gate reconciliation portal (`Titanium Enterprise v3.0 Release`).

### Key Capabilities & Interface
- **Linear / Jira Project Management Interface**:
  - **Left Sidebar**: Project switcher (`Titanium Enterprise v3.0`), Milestone filtering (`v3.0 Cutover Gate` - M006), Views (`Kanban Board`, `List View`), and quick filters.
  - **Interactive Kanban Board**: Visual columns for `BLOCKED` (alert priority), `PENDING`, `IN_PROGRESS`, and `COMPLETED`.
  - **Sortable List Table**: Full table view with status indicators, priority tags (`URGENT`, `HIGH`, `MEDIUM`, `LOW`), assignee identities, and subtask counts.
  - **Task Detail Drawer**: Collapsible panel to examine full task specifications, reassign overloaded engineers, edit task states, and visualize upstream/downstream dependencies with cycle detection.
  - **Cutover Handover Modal**: Formal sign-off interface to review reconciled task IDs and post the authoritative `READY` vs `BLOCKED` recommendation.
- **Dual Interaction Modes**: Direct FastMCP stdio server for LLM agents, and REST API routes under `/api/tasks/...` for web and multimodal agents.

---

## Scenario: Titanium Enterprise v3.0 Release Blocker Reconciliation

As the Lead SRE and Release Auditor:
1. **Break Disaster Recovery Deadlocks**: Discover and unlink circular dependency cycles between `TASK043`, `TASK044`, and `TASK048` blocking snapshot automation and recovery drills.
2. **Clear Stale Compliance Gates**: Verify third-party SOC-2 audit evidence (`TASK047`) to unblock dependent verification tracks (`TASK040`).
3. **Escalate Concurrency Defects**: Reassign and escalate the token revocation race condition under load (`TASK042`) to Senior Auth engineering.
4. **Deduplicate Cache Tickets**: Identify redundant pool exhaustion reports (`TASK052` duplicate of `TASK051`) to avoid fragmented triage.
5. **Submit Handover Sign-Off**: Record the list of reconciled tasks and the authoritative cutover decision.

---

## Running Locally

### Development Server (Next.js)
```bash
cd task_manager-ui
npm install
npm run dev # Starts web UI on http://localhost:3004
```

### Self-Tests & Verifier
```bash
./tests/test.sh
```

### Reference Solution Oracle
```bash
./solution/solve.sh
```

### Harbor Run
```bash
./run.sh
```
