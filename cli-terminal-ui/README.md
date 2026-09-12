# OpenGym: CLI Terminal UI Environment (`cli-terminal-ui`)

Interactive Web Terminal & Server Administration Console for AI agent evaluation and training under the [Harbor](https://github.com/avahr/harbor) framework.

## Overview

`cli-terminal-ui` provides a web-based DevOps diagnostics and remediation interface simulating an enterprise Linux production host (`app-node-04.prod.corp`) suffering from severe cascading degradation.

### Key Capabilities & Interface
- **Interactive Terminal Console**: Web terminal with live shell command execution, colored output streams (stdout/stderr), history navigation, and quick diagnostic chips.
- **Real-Time Telemetry Bar**: Live CPU load dial, memory consumption gauge, root filesystem storage pressure gauge, and critical service status indicator.
- **Process Management Table**: Process viewer with PID, user, CPU%, memory, and instant 1-click process termination.
- **Systemd Service Cards**: Status badges and restart controls for `payment-processor`, `nginx`, `sshd`, and `systemd-journald`.
- **Filesystem Inspector**: Interactive file explorer to examine configuration files (`/etc/payment-processor/config.yaml`), SSL keys (`/etc/ssl/certs/payment-api.key`), and diagnostic logs.
- **Incident Remediation Submission**: Structured triage report submission form with root-cause summary and executed actions.
- **Dual Interaction Modes**: Direct FastMCP stdio server for LLM agents, and REST API routes under `/api/terminal/...` for web / browser agents.

---

## Scenario: Production Payment Service Failure & Host Exhaustion

The production server `app-node-04.prod.corp` is experiencing a critical SEV-1 incident:
1. **Rogue Worker Process**: A runaway Python script (`worker-leak.py`, PID `4921`) has consumed 94.8% CPU and is leaking memory.
2. **Disk Exhaustion**: Runaway debug traces have bloated `/var/log/app/debug_trace.log` to over 18.8 MB, leaving the root partition at 96.7% full.
3. **Misconfigured Database Connection**: `/etc/payment-processor/config.yaml` points to `db-replica-invalid.internal:9999` instead of `db-primary.internal:5432`.
4. **Insecure TLS Key Permissions**: The private key `/etc/ssl/certs/payment-api.key` has unsafe permissions `0666` instead of `0600` or `0400`.
5. **Downed Payment Service**: `payment-processor.service` is failed and refuses to start until configuration and file permissions are corrected.

---

## Running Locally

### Development Server (Next.js)
```bash
cd cli-terminal-ui
npm install
npm run dev # Starts web UI on http://localhost:3002
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
