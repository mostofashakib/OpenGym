# Terminal — Headless CLI Environment

A deterministic, high-fidelity headless CLI terminal environment for evaluating AI agents on systems administration, incident triage, and production service recovery.

## The Task

At 02:15 UTC, automated monitoring triggered high-severity alerts on production host `app-node-04.prod.corp`. Core transaction processing is down, disk capacity is nearing total exhaustion (98% full), and on-call notes report conflicting diagnoses.

The agent must:
1. **Process Triage**: Discover and terminate the rogue background worker (`worker-leak.py` with PID `4921`) leaking memory and CPU.
2. **Disk Space Reclamation**: Truncate or remove the runaway debug dump in `/var/log/app/debug_trace.log` to restore >70% free disk capacity.
3. **Configuration Repair**: Review `/etc/payment-processor/config.yaml`, fix invalid database parameters (`host: db-primary.internal`, `port: 5432`), and revert broken replica settings.
4. **Security Hardening**: Enforce strict file permissions (`0600`) on `/etc/ssl/certs/payment-api.key`.
5. **Service Restoration**: Restart `payment-processor.service` and verify that status is `active (running)`.
6. **Remediation Sign-Off**: Submit final incident post-mortem and resolution report via `submit_task`.

## Tools

The agent interacts via an MCP server (`terminal-mcp`) providing:
- `run_command(command, cwd)`: Execute POSIX commands (`ps`, `kill`, `df`, `ls`, `cat`, `grep`, `find`, `chmod`, `systemctl`, `head`, `tail`, `wc`, `sed`).
- `read_file(path, offset, limit)`: Read file lines.
- `write_file(path, content, mode)`: Write or append text to files.
- `list_processes(status)`: Enumerate processes and resource metrics.
- `inspect_system()`: Retrieve system metrics and service statuses.
- `submit_task(summary, actions_taken)`: Record final resolution.

## Running

```bash
# Deterministic reference oracle run (scores 1.000)
harbor run -p ./cli-terminal -a oracle

# Run with Ollama model
./cli-terminal/run.sh

# Run with hosted models via OpenRouter
MODEL=openrouter/anthropic/claude-3.5-sonnet ./cli-terminal/run.sh

# Run self-tests and verifier
./cli-terminal/tests/test.sh
```
