# OpenGym: Slack UI Environment (`slack-ui`)

Interactive Enterprise Slack Web Client and Agent Environment for RL and agent benchmarking under the [Harbor](https://github.com/avahr/harbor) framework.

## Overview

`slack-ui` provides a web-based Slack communication workspace modeling enterprise software coordination, debugging investigations, code reviews, and cross-functional cutover decisions.

### Key Capabilities & Interface
- **Modern Slack Workspace Interface**:
  - **Left Sidebar**: Workspace switcher (`Acme Engineering`), Channels list (`#debugging`, `#acme-migration`, `#identity-eng`, `#data-ops`, `#general`, `#incidents`) with real-time unread badges, direct messages (`daniel`, `alyssa`, `sophia`, `marcus`), and user profile (`agent / Senior Staff Engineer`).
  - **Channel Header**: Channel name, topic, member counts, search bar, and action triggers.
  - **Interactive Message Stream**: Chronological messages with markdown rendering, code formatting, avatar color-coding, and inline reply counts (`💬 4 replies`).
  - **Collapsible Thread Drawer**: Side panel for deep inspection of thread discussions and posting inline replies.
  - **Code Review Assistant**: In `#debugging`, interactive PR review tools allowing one-click `Looks good to me` approvals or inline defect critiques.
  - **Cutover Decision Modal**: Form to post the final authoritative readiness assessment into Daniel's request thread (`MSG145`).
- **Dual Interaction Modes**: Direct FastMCP stdio server for LLM agents, and REST API routes under `/api/slack/...` for web and multimodal agents.

---

## Scenario: Acme Enterprise Migration Cutover

As the Senior Staff Engineer on the Acme migration:
1. **Reconstruct True State**: Investigate `#acme-migration`, `#identity-eng`, and `#data-ops` to verify SSO certificate rotation, historical data backfills, EU workspace permissions, and the cutover window.
2. **Clear Code Review Queue**: In `#debugging`, review all open `[review-needed]` code revision threads. Approve correct PRs with `Looks good to me` and critique material defects.
3. **Submit Final Assessment**: Reply in Daniel's original request thread with the confirmed migration window, `READY` or `BLOCKED`, area owners, and next actions.

---

## Running Locally

### Development Server (Next.js)
```bash
cd slack-ui
npm install
npm run dev # Starts web UI on http://localhost:3003
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
